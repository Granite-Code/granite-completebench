> [!NOTE]
> See the [granite-completebench website](https://granite-code.github.io/granite-completebench/) to explore the data.

# granite-completebench

This is an evaluation tool for how LLM models work for code autocompletio.
granite-completebench is used for the development of
[Granite.Code](https://granitecode.ai).
In particular, we're interested in the combination of:

- Prompts and postprocessing in the style of [Continue](https://www.continue.dev/).
- The [IBM Granite Models](https://www.ibm.com/granite)

However, other models are included here for comparison.

## CrossCodeEval relationship

The dataset and some of the evaluation and inference code comes from [CrossCodeEval](https://crosscodeeval.github.io/).
However, the usage is a bit different.
In particular,
we're looking at "fill in the middle" behavior where both a prefix _and_ a suffix are used.
While the CrossCodeEval dataset includes suffixes,
they were not used during generation,
allowing models without FIM support to be evaluated.
For this and other reasons,
the metrics we measure here will be different than reported for CrossCodeEval.

## Limitations

The CrossCodeEval dataset is testing completion only in a very limited circumstance:
completing from a point within a line to the end of the same line.
In addition,
the snippets included with the CrossCodeEval dataset do not typically include sufficient information to determine an exact matching completion.
Performance of models in other circumstances might be different.

The metrics do not execute or even parse the generated code,
we're just looking for an exact match or textually similar code.

## Installation

- Create a virtualenv and install dependencies:

      python3.11 -m venv .venv && . .venv/bin/activate
      pip install -e .
      # For inference via vllm
      pip install -e .[vllm]

- Uncompress the CrossCodeEval data:

      tar -xvJf data/crosscodeeval_data.tar.xz -C data/`

## Generating model outputs

```sh
granite-codebench generate-vllm \
    --model=granite3.3:8b-base \
    --task=line_completion_rg1_openai_cosine_sim \
    --temperature=0 \
    --language=java \
    --template=comment
```

(The openai_cosine_sim task is used because in the CrossCodeEval paper,
this method of producing RAG snippets to include for the model worked
slightly better than the alternatives they tested.)

## Evaluating model outputs

```sh
granite-codebench evaluate \
    --model=granite3.3:8b-base \
    --task=line_completion_rg1_openai_cosine_sim \
    --language=java \
    --template=comment \
    --postprocess=truncate_suffix_comment
```
