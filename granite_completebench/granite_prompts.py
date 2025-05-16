from dataclasses import dataclass
import json
from pathlib import Path
from textwrap import dedent
from typing import Literal, TypedDict

from transformers import AutoTokenizer, PreTrainedTokenizer

from .file_utils import read_jsonl


from .types import Example


@dataclass
class AutocompleteOptions:
    prefix_percentage: float = 0.3
    max_suffix_percentage: float = 0.2
    max_prompt_tokens = 1024
    template: Literal["no_snippets", "inside", "outside", "comment"] = "outside"


DEFAULT_CONFIG = AutocompleteOptions()


def truncate(
    text: str, max_num_tokens: int, side: Literal["left", "right"], tokenizer: PreTrainedTokenizer
) -> str:
    """Truncate prompt from side given the token budget"""

    tokens = tokenizer.tokenize(text)
    num_tokens = len(tokens)

    if num_tokens > max_num_tokens:
        if side == "left":
            prompt_tokens = tokens[num_tokens - max_num_tokens :]
        elif side == "right":
            prompt_tokens = tokens[:max_num_tokens]
        text = tokenizer.convert_tokens_to_string(prompt_tokens)

    return text


def prune_lines_from_top(text: str, max_num_tokens: int, tokenizer: PreTrainedTokenizer):
    pruned_text = truncate(text, max_num_tokens, "left", tokenizer)
    pruned_prefix = text[: len(text) - len(pruned_text)]
    if pruned_prefix == "" or pruned_prefix[-1] == "\n":
        return pruned_text
    first = pruned_text.find("\n")
    if first >= 0:
        return pruned_text[first + 1 :]
    else:
        return ""


def prune_lines_from_bottom(text: str, max_num_tokens: int, tokenizer: PreTrainedTokenizer):
    pruned_text = truncate(text, max_num_tokens, "right", tokenizer)
    pruned_suffix = text[-(len(text) - len(pruned_text)) :]
    if (
        pruned_suffix == ""
        or (pruned_text != "" and pruned_text[-1] == "\n")
        or pruned_suffix[0] == "\n"
    ):
        return pruned_text
    last = pruned_text.rfind("\n")
    if last >= 0:
        return pruned_text[0 : last + 1]
    else:
        return ""


def count_tokens(text: str, tokenizer: PreTrainedTokenizer):
    return len(tokenizer.tokenize(text))


# continue/core/autocomplete/utils/HelperVars.ts:prunePrefixSuffix
def prune_prefix_suffix(
    prefix: str, suffix: str, tokenizer: PreTrainedTokenizer, options: AutocompleteOptions
):
    # Construct basic prefix
    max_prefix_tokens = int(options.max_prompt_tokens * options.prefix_percentage)
    pruned_prefix = prune_lines_from_top(
        prefix,
        max_prefix_tokens,
        tokenizer,
    )

    # Construct suffix
    max_suffix_tokens = int(
        min(
            options.max_prompt_tokens - count_tokens(pruned_prefix, tokenizer),
            options.max_suffix_percentage * options.max_prompt_tokens,
        )
    )

    pruned_suffix = prune_lines_from_bottom(
        suffix,
        max_suffix_tokens,
        tokenizer,
    )

    return (
        pruned_prefix,
        pruned_suffix,
    )


def get_fim_pad_token(tokenizer: PreTrainedTokenizer):
    all_added_tokens = set(v.content for v in tokenizer.added_tokens_decoder.values())

    if "<|fim_pad|>" in all_added_tokens:
        return "<|fim_pad|>"
    else:
        return None


def get_filename_token(tokenizer: PreTrainedTokenizer):
    all_added_tokens = set(v.content for v in tokenizer.added_tokens_decoder.values())

    if "<filename>" in all_added_tokens:
        return "<filename>"
    elif "<|file_sep|>" in all_added_tokens:
        return "<|file_sep|>"
    else:
        raise RuntimeError("Can't find filename special token")


def create_prompt(
    example: Example, tokenizer: PreTrainedTokenizer, options: AutocompleteOptions = DEFAULT_CONFIG
):
    all_added_tokens = set(v.content for v in tokenizer.added_tokens_decoder.values())
    if "<fim_prefix>" in all_added_tokens:
        fim_prefix = "<fim_prefix>"
        fim_suffix = "<fim_suffix>"
        fim_middle = "<fim_middle>"
    elif "<|fim_prefix|>" in all_added_tokens:
        fim_prefix = "<|fim_prefix|>"
        fim_suffix = "<|fim_suffix|>"
        fim_middle = "<|fim_middle|>"
    else:
        raise RuntimeError("Can't find special FIM tokens")

    filename = get_filename_token(tokenizer)

    prefix, suffix = prune_prefix_suffix(
        example["prompt"], example["right_context"], tokenizer, options
    )

    if options.template == "none":
        prompt = (
            fim_prefix
            + f"{filename}{example['metadata']['file']}\n"
            + prefix
            + fim_suffix
            + suffix
            + fim_middle
        )
    elif options.template == "comment":
        comment = "# " if example["metadata"]["file"].endswith(".py") else "// "

        def add_comment_markers(text):
            return "\n".join(comment + line for line in text.strip().split("\n"))

        snippet_text = "\n".join(
            f"{comment}Path: {item['filename']}\n{add_comment_markers(item['retrieved_chunk'])}"
            for item in example["crossfile_context"]["list"]
        )
        # Failsafe in case of bad snippets
        snippet_text = prune_lines_from_bottom(snippet_text, 1024, tokenizer)

        prompt = (
            fim_prefix
            + snippet_text
            + f"{comment}{example['metadata']['file']}\n"
            + prefix
            + fim_suffix
            + suffix
            + fim_middle
        )
    else:
        # The prefix here prevents a weirdness with granite-3.3-8b-instruct where if the
        # the completion starts with <filename>, the model goes off the rails
        snippet_text = (
            "Please keep response concise and scope of response limited. "
            + "If no good completion exists, do not answer:\n"
            + "\n".join(
                f"{filename}{item['filename']}\n{item['retrieved_chunk'].strip()}"
                for item in example["crossfile_context"]["list"]
            )
        )
        # Failsafe in case of bad snippets
        snippet_text = prune_lines_from_bottom(snippet_text, 2048, tokenizer)

        prefix, suffix = prune_prefix_suffix(
            example["prompt"], example["right_context"], tokenizer, options
        )

        if options.template == "inside":
            prompt = (
                fim_prefix
                + snippet_text
                + f"{filename}{example['metadata']['file']}\n"
                + prefix
                + fim_suffix
                + suffix
                + fim_middle
            )
        else:
            prompt = (
                snippet_text
                + f"{filename}{example['metadata']['file']}\n"
                + fim_prefix
                + prefix
                + fim_suffix
                + suffix
                + fim_middle
            )

    return prompt


if __name__ == "__main__":
    file = Path(__file__).parent.parent / "data/python/line_completion_rg1_openai_cosine_sim.jsonl"
    model = "ibm-granite/granite-3.3-8b-base"
    #  model = "Qwen/Qwen2.5-Coder-14B"
    tokenizer = AutoTokenizer.from_pretrained(model)
    example: Example
    for example in read_jsonl(file):
        prompt = create_prompt(example, tokenizer, AutocompleteOptions(template="outside"))
        # print(prompt)
