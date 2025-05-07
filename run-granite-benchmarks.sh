#!/usr/bin/bash

models=(
  ibm-granite/granite-3.3-8b-base
  ibm-granite/granite-3.3-8b-instruct
  ibm-granite/granite-3.3-2b-base
)

languages=(
  csharp
  java
  python
  typescript
)

snippet_types=(
  none
  outside
  inside
  comment
)

task=line_completion_rg1_openai_cosine_sim
output_dir=granite-outputs/

for model in ${models[@]} ; do
  echo python scripts/vllm_inference_granite.py \
    --model $model \
    --task $task \
    --output_dir $output_dir \
    ${languages[@]/#/--language=} \
    ${snippet_types[@]/#/--snippet_type=}
done
