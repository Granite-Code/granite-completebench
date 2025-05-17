## Template

- **no_snippets** - No RAG snippets are included.
- **comment** - Snippets are part of the FIM prefix, commented out.
- **inside** - Snippets are part of the FIM prefix, deliminated by `<filename>` or `<|file_sep|>`.
- **inside** - Snippets are before the FIM template, deliminated by `<filename>` or `<|file_sep|>`.

## Postprocess

- **none** - No postprocessing
- **truncate_suffix** - If the generated code matches the start of the suffix, truncate it. (One of Continue's postprocessing steps.)
- **truncate_suffix_close** - As with truncate_suffix, but additionally, if the suffix starts with a close character, or dedent, truncate the output at the end of the block.
- **truncate_expression** - Truncate the generated output at the end of a single expression. (CrossCodeEval behavior - does not test FIM completion well.)

## Metrics

- **Exact Match %** - Percentage of cases where the output after postprocessing is identical to the original code.
- **Edit Similarity** - Average Levenshtein distance between the generated and original code, normalized by the length of the original code.
- **Stop %** - Percentage of cases where the model stops generating before hitting the token limit, or where postprocessing finds a place to cut the output short.
