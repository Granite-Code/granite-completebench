#!/usr/bin/bash

set -e

models=(
  ibm-granite/granite-3.3-8b-base
  ibm-granite/granite-3.3-8b-instruct
  ibm-granite/granite-3.3-2b-base
  Qwen/Qwen2.5-Coder-14B
)

languages=(
  csharp
  java
  python
  typescript
)

templates=(
  no_snippets
  outside
  inside
  comment
)

task=line_completion_rg1_openai_cosine_sim
output_dir=granite-outputs/

for model in ${models[@]} ; do
  python scripts/vllm_inference_granite.py \
    --model $model \
    --task $task \
    --output_dir $output_dir \
    --temperature 0 \
    ${languages[@]/#/--language=} \
    ${templates[@]/#/--template=}
done
