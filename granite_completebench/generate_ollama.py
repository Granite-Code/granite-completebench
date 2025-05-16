from functools import partial
import json
from multiprocessing import Pool
import os
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import requests
from tqdm import tqdm
from transformers import AutoTokenizer, PreTrainedTokenizer

from granite_completebench.granite_prompts import (
    AutocompleteOptions,
    create_prompt,
    get_filename_token,
    get_fim_pad_token,
)

from .cli import GenerateOllamaArgs
from .file_utils import read_jsonl, write_jsonl
from .types import Example, Prediction


def generate_one(
    args: GenerateOllamaArgs, ollama_model: str, stop: list[str], item: tuple[Example, str]
):
    d, prompt = item

    ollama_host = os.getenv("OLLAMA_HOST", default="http://localhost:11434")
    response = requests.post(
        f"{ollama_host}/api/generate",
        json={
            "raw": True,
            "model": ollama_model,
            "prompt": prompt,
            "options": {
                "temperature": args.temperature,
                "top_p": args.top_p,
                "num_predict": args.generation_max_tokens,
                "stop": stop,
            },
            "stream": False,  # Return a single response object
        },
    )

    response.raise_for_status()
    json_response = response.json()

    if json_response["prompt_eval_count"] == args.generation_max_tokens:
        stop_reason = "length"
    else:
        stop_reason = "stop"

    return Prediction(
        task_id=d["metadata"]["task_id"],
        templated=prompt,
        output=json_response["response"],
        stop_reason=stop_reason,
    )


def generate(
    args: GenerateOllamaArgs,
    data: list[Example],
    ollama_model: str,
    tokenizer: PreTrainedTokenizer,
    options: AutocompleteOptions,
    output_file: Path,
):
    ollama_host = os.getenv("OLLAMA_HOST", default="http://localhost:11434")

    stop: list[str] = [
        cast(str, tokenizer.eos_token),
        get_filename_token(tokenizer),
    ]
    fim_pad_token = get_fim_pad_token(tokenizer)
    if fim_pad_token is not None:
        stop.append(fim_pad_token)

    prompts = []
    for d in tqdm(data, desc="Generating prompts"):
        prompt = create_prompt(d, tokenizer, options)
        prompts.append(prompt)

    predictions: list[Prediction] = []

    process_item = partial(generate_one, args, ollama_model, stop)
    with Pool(4) as pool:
        predictions = list(tqdm(pool.imap(process_item, zip(data, prompts)), total=len(prompts)))

    with write_jsonl(output_file, create_parents=True) as writer:
        for d in predictions:
            writer.append(d)


def generate_for_model(args: GenerateOllamaArgs, model: str, ollama_model: str):
    model_short = model.split("/")[-1]

    tokenizer = AutoTokenizer.from_pretrained(model, trust_remote_code=True)
    if tokenizer is None:
        raise ValueError(f"Could not load tokenizer for {model}")

    # generation
    for language in args.language:
        data_path = Path(args.data_root_dir) / language / (args.task + ".jsonl")
        data = [l for l in read_jsonl(data_path)]

        for template in args.template:
            print(f"====== model={ollama_model} language={language} template={template}")
            output_file = (
                Path(args.output_dir) / model_short / language / template / "prediction.jsonl"
            )
            if os.path.exists(output_file):
                continue

            options = AutocompleteOptions(template=template)
            generate(args, data, ollama_model, tokenizer, options, output_file)


def command(args: GenerateOllamaArgs):
    print(json.dumps(vars(args), indent=4))
    for model, ollama_model in zip(args.model, args.ollama_model):
        generate_for_model(args, model, ollama_model)


__all__ = ["command"]
