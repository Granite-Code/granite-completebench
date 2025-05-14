import json
import os
from typing import cast

from tqdm import tqdm
from transformers import AutoTokenizer, PreTrainedTokenizer
from transformers.utils import logging
from vllm import LLM, SamplingParams

from .types import Example, Prediction
from .granite_prompts import create_prompt, AutocompleteOptions, get_filename_token
from .cli import GenerateVllmArgs


def get_fim_pad_token(tokenizer: PreTrainedTokenizer):
    all_added_tokens = set(v.content for v in tokenizer.added_tokens_decoder.values())

    if "<|fim_pad|>" in all_added_tokens:
        return "<|fim_pad|>"
    else:
        return None


def generate(
    data: list[Example],
    tokenizer: PreTrainedTokenizer,
    options: AutocompleteOptions,
    sampling_params: SamplingParams,
    llm: LLM,
    output_file: str,
):
    prompts = []
    for d in tqdm(data, desc="Generating prompts"):
        prompt = create_prompt(d, tokenizer, options)
        prompts.append(prompt)

    outputs = llm.generate(prompts, sampling_params, use_tqdm=True)

    filename_token = get_filename_token(tokenizer)
    fim_pad_token = get_fim_pad_token(tokenizer)
    eos_token = tokenizer.eos_token
    assert isinstance(eos_token, str)

    with open(output_file, "w") as f:
        for d, prompt, response in tqdm(zip(data, prompts, outputs)):
            output = response.outputs[0].text
            if output.endswith(eos_token):
                output = output.removesuffix(eos_token)
                stop_reason = "stop:eos"
            elif output.endswith(filename_token):
                output = output.removesuffix(filename_token)
                stop_reason = "stop:filename"
            elif fim_pad_token is not None and output.endswith(fim_pad_token):
                output = output.removesuffix(fim_pad_token)
                stop_reason = "stop:pad"
            else:
                assert len(response.outputs[0].token_ids) == sampling_params.max_tokens
                stop_reason = "length"

            prediction: Prediction = {
                "task_id": d["metadata"]["task_id"],
                "templated": prompt,
                "output": output,
                "stop_reason": stop_reason,
            }
            print(json.dumps(prediction), file=f, flush=True)


def generate_for_model(args: GenerateVllmArgs, model: str):
    model_short = model.split("/")[-1]

    # load model
    llm = LLM(model=model, tensor_parallel_size=args.tp_size, max_model_len=args.model_max_tokens)
    tokenizer: PreTrainedTokenizer = AutoTokenizer.from_pretrained(
        args.model, trust_remote_code=True
    )

    stop_token_ids = [
        tokenizer.eos_token_id,
        cast(int, tokenizer.convert_tokens_to_ids(get_filename_token(tokenizer))),
    ]
    fim_pad_token = get_fim_pad_token(tokenizer)
    if fim_pad_token is not None:
        stop_token_ids.append(cast(int, tokenizer.convert_tokens_to_ids(fim_pad_token)))
    sampling_params = SamplingParams(
        temperature=args.temperature,
        top_p=args.top_p,
        stop_token_ids=stop_token_ids,
        skip_special_tokens=False,
        include_stop_str_in_output=True,
        max_tokens=args.generation_max_tokens,
    )

    # setup paths
    if not os.path.isdir(args.output_dir):
        print(f"==== Output dir does not exist. Creating: {args.output_dir} ====")
        os.makedirs(args.output_dir)

    # generation
    for language in args.language:
        data_path = os.path.join(args.data_root_dir, language, args.task + ".jsonl")
        data = [json.loads(l) for l in open(data_path, "r").readlines()]

        for template in args.template:
            print(f"====== model={args.model} language={language} template={template}")
            output_file = os.path.join(
                args.output_dir, f"prediction_{model_short}_{language}_snippet_{template}.jsonl"
            )
            if os.path.exists(output_file):
                continue
            options = AutocompleteOptions(template=template)
            generate(data, tokenizer, options, sampling_params, llm, output_file)


def command(args: GenerateVllmArgs):
    print(json.dumps(vars(args), indent=4))
    for model in args.model:
        generate_for_model(args, model)


__all__ = ["command"]
