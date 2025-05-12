
# Copyright Amazon.com, Inc. or its affiliates. All rights reserved.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import argparse
import json
import logging
import os

from eval_metric import compute_metric_stmt

import pandas


logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

HTML_HEAD="""\
<DOCTYPE!>
<html>
<head>
  <style>
table {
    row-gap: 0px;
    column-gap: 0px;
    border-collapse: collapse;
    border: 1px solid #ccc;
    font-family: monospace;
}

td {
    border: 0px;
    margin: 0px;
    padding: 2px;
    text-align: right;
    width: 75px;
}

th {
    border: 1px solid #ccc;
    background: #fff;
}

tr:nth-child(odd) td {
    background: #eee;
}
  </style>
</head>
<body>
"""

HTML_FOOT="""\
</body>
</html>
"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # model inference args
    parser.add_argument(
        '--task', type=str, required=True,
    )
    parser.add_argument(
        '--language', type=str, required=True,
        choices=['csharp', 'python', 'java', 'typescript'],
        action='append'
    )
    parser.add_argument(
        '--snippet-type', type=str, choices=['none', 'inside', 'outside', 'comment'],
        action='append', required=True,
        help='way RAG snippets are presented to the model'
    )
    parser.add_argument(
        '--data_root_dir', type=str, default='data/',
        help='path to directory where data is organized in lang/task.jsonl format'
    )
    parser.add_argument(
        '--output_dir', type=str, required=True,
        help='path to directory where to generation outputs are stored'
    )
    parser.add_argument(
        '--results_dir', type=str, required=True,
        help='path to directory where to evaluation results are stored'
    )
    parser.add_argument(
        '--model', type=str,
        action='append', required=True,
        help='vLLM-supported model'
    )
    parser.add_argument(
        '--truncate', type=str, choices=['none', 'expression', 'suffix', 'close'],
        action='append',
        help='way to truncate the prediction (expression if nonet given)'
    )
    args = parser.parse_args()

    if len(args.truncate) == 0:
        args.truncate = ['expression']
    else:
        try:
            pos = args.truncate.index('none')
            args.truncate = args.truncate[pos + 1:]
        except ValueError:
            pass

    os.makedirs(args.results_dir, exist_ok=True)

    results = []

    for model in args.model:
        for language in args.language:
            for snippet_type in args.snippet_type:
                model_short = model.split("/")[-1]
                prompt_file = os.path.join(args.data_root_dir, language, args.task + '.jsonl')
                output_file = os.path.join(args.output_dir, f"prediction_{model_short}_{language}_snippet_{snippet_type}.jsonl")
                results_base = os.path.join(args.results_dir, f"{model_short}_{language}_snippet_{snippet_type}")
                results_file = results_base + "_results.json"
                if os.path.exists(results_file):
                    with open(results_file, "r") as f:
                        res = json.load(f)
                else:
                    res = compute_metric_stmt(output_file, results_base, prompt_file, language, truncate=args.truncate)
                annotated_res = dict(
                    **res,
                    model=model.split("/")[-1],
                    language=language,
                    snippet_type=snippet_type,
                )
                results.append(annotated_res)

    metrics = ["em", "es", "stop"]
    short_models = [model.split("/")[-1] for model in args.model]

    dataframe = pandas.DataFrame(results)
    grouped = pandas.pivot_table(dataframe, values=metrics, index=["model", "snippet_type"], columns=["language"])

    # Calculate the mean across language columns for each metric and add it to the pivot table

    for metric in metrics:
        # Get the mean across all languages for this metric
        mean_values = grouped.xs(metric, axis=1, level=0).mean(axis=1).round(2)
        # Add the mean as a new column with language = 'Average'
        grouped[(metric, 'Average')] = mean_values

    def key_function(x):
        print(x)
        return metrics.index(x)

    grouped = grouped.sort_index(axis=1, level=0, sort_remaining=False, key=lambda ind: ind.map(lambda v: metrics.index(v)))
    grouped = grouped.sort_index(axis=0, level=1, sort_remaining=False, key=lambda ind: ind.map(lambda v: args.snippet_type.index(v)))
    grouped = grouped.sort_index(axis=0, level=0, sort_remaining=False, key=lambda ind: ind.map(lambda v: short_models.index(v)))
    grouped = grouped.rename(columns={"em": "Exact Match %", "es": "Edit Similarity", "stop": "Stop %"}, level=0)

#    If we want to sort first by language, then by metric type
#    grouped = grouped.swaplevel(0, 1, axis=1)
#    grouped = grouped.sort_index(axis=1, level=0)
    print(grouped)
    with open(os.path.join(args.results_dir, "summary.txt"), "w") as f:
        print(grouped, file=f)
    with open(os.path.join(args.results_dir, "summary.html"), "w") as f:
        print(HTML_HEAD, file=f, end="")
        print(grouped.to_html(), file=f)
        print(HTML_FOOT, file=f, end="")
