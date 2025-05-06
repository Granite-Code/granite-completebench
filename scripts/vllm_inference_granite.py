"""
Script to run vllm-based inference. See README for an example.
"""

import argparse
import json
import os
from typing import List

from tqdm import tqdm
from transformers import AutoTokenizer
from transformers.utils import logging
from vllm import LLM, SamplingParams

from .granite_prompts import create_prompt, Example, AutocompleteOptions

logging.set_verbosity_info()
logger = logging.get_logger(__name__)
# add a small buffer to take care of non-lossless tokenizers
BUFFER = 100



def cceval_generate(
        args,
        data,
        tokenizer,
        options: AutocompleteOptions,
        sampling_params,
        llm
):
    prompts = []
    for d in data:
        prompt = create_prompt(d, tokenizer, options)

    outputs = llm.generate(prompts, sampling_params, use_tqdm=True)

    out_path = os.path.join(args.output_dir, 'prediction.jsonl')
    with open(out_path, 'w') as f:
        for d, response in tqdm(zip(data, outputs)):
            d['pred'] = response.outputs[0].text
            d['task_id'] = d['metadata']['task_id']
            print(json.dumps(d), file=f, flush=True)


def main():
    # set the OpenAI key
    # openai.api_key = os.environ.get('OPENAI_KEY', None)
    # if openai.api_key is None:
    #    raise ValueError('OPENAI_KEY environment variable not set')

    # get config for current run
    parser = argparse.ArgumentParser()
    parser.add_argument('--temperature', type=float, default=0.2)

    parser.add_argument('--top_p', type=float, default=0.95)
    parser.add_argument(
        '--task', type=str, required=True,
    )
    parser.add_argument(
        '--language', type=str, required=True,
        choices=['csharp', 'python', 'java', 'typescript']
    )
    parser.add_argument(
        '--data_root_dir', type=str, default='data/',
        help='path to directory where data is organized in lang/task.jsonl format'
    )
    parser.add_argument(
        '--output_dir', type=str, required=True,
        help='path to directory where to store outputs'
    )
    parser.add_argument(
        '--model', type=str, required=True,
        help='vLLM-supported model'
    )
    parser.add_argument(
        '--tp_size', type=int, default=1,
        help='tensor parallel size'
    )
    parser.add_argument(
        '--generation_max_tokens', type=int, default=50,
        help='maximum number of tokens to generate'
    )

    args = parser.parse_args()
    print(json.dumps(vars(args), indent=4))

    # load model
    llm = LLM(model=args.model, tensor_parallel_size=args.tp_size, max_model_len=args.model_max_tokens)
    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    sampling_params = SamplingParams(temperature=args.temperature, top_p=args.top_p, max_tokens=args.generation_max_tokens)

    # setup paths
    if not os.path.isdir(args.output_dir):
        print(f'==== Output dir does not exist. Creating: {args.output_dir} ====')
        os.makedirs(args.output_dir)
    data_path = os.path.join(args.data_root_dir, args.language, args.task + '.jsonl')
    data = [json.loads(l) for l in open(data_path, 'r').readlines()]

    # generation
    options = AutocompleteOptions()
    cceval_generate(args, data, tokenizer, options, sampling_params, llm)


if __name__ == '__main__':
    main()
