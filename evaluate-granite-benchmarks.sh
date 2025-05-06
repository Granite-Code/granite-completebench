#!/usr/bin/bash

set -e

models=(
  ibm-granite/granite-3.3-8b-base
  ibm-granite/granite-3.3-8b-instruct
  ibm-granite/granite-3.3-2b-base
  Qwen/Qwen2.5-Coder-14B
  Qwen/Qwen2.5-Coder-7B
  Qwen/Qwen2.5-Coder-3B
)
# models=(ibm-granite/granite-3.3-8b-base)

languages=(
  csharp
  java
  python
  typescript
)
# languages=(java)

templates=(
  no_snippets
  comment
  inside
  outside
)
# snippet_types=(inside)

postprocessors=(
  none
  truncate_suffix
  truncate_suffix_close
  truncate_expression
)

task=line_completion_rg1_openai_cosine_sim

granite-completebench evaluate \
    --update-web \
    --task $task \
    "${models[@]/#/--model=}" \
    "${languages[@]/#/--language=}" \
    "${templates[@]/#/--template=}" \
    "${postprocessors[@]/#/--postprocess=}"

