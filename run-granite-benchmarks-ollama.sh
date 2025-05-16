#!/usr/bin/bash

set -e

models=(
  "ibm-granite/granite-3.3-8b-base owtaylor/granite3.3:8b-base"
  "ibm-granite/granite-3.3-8b-instruct granite3.3:8b"
  "ibm-granite/granite-3.3-2b-base; owtaylor/granite3.3:2b-base"
  "Qwen/Qwen2.5-Coder-14B qwen2.5-coder:14b"
  "Qwen/Qwen2.5-Coder-7B qwen2.5-coder:7b"
  "Qwen/Qwen2.5-Coder-3B qwen2.5-coder:3b"
)
models=("ibm-granite/granite-3.3-8b-instruct granite3.3:8b")

languages=(
  csharp
  java
  python
  typescript
)
languages=("python")

templates=(
  no_snippets
  outside
  inside
  comment
)
templates=("outside")

task=line_completion_rg1_openai_cosine_sim
output_dir=granite-outputs/

for model in "${models[@]}" ; do
  read hf ollama < <(echo $model)
  granite-completebench generate-ollama \
    --task $task \
    --model=$hf --ollama-model=$ollama \
    --output-dir=outputs-ollama \
    --temperature 0 \
    ${languages[@]/#/--language=} \
    ${templates[@]/#/--template=}
done
