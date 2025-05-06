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

from argparse import ArgumentTypeError
import json
import os
from pathlib import Path
import random
from venv import create

import pandas

from .cli import EvaluateArgs
from .eval_metric import compute_metric_stmt
from .file_utils import read_json, read_jsonl, write_json, write_jsonl
from .postprocess import PostProcessor, create_postprocessor
from .paths import get_output_path, get_prompt_path, get_result_dir
from .types import Example, LabelledMetrics, LabelledPrediction, LabelledResult, Metrics, Prediction


def evaluate(
    args: EvaluateArgs, model: str, language: str, template: str, postprocessor: PostProcessor
) -> LabelledMetrics | None:
    results: list[LabelledMetrics] = []

    model_short = model.split("/")[-1]
    prompt_file = get_prompt_path(args, language)
    output_file = get_output_path(args, model, language, template)
    if not output_file.exists():
        print("No output file found for", output_file)
        return None

    result_dir = get_result_dir(
        args, model, language, template, postprocessor.name, create_dir=True
    )

    results_file = result_dir / "results.json"
    if results_file.exists():
        res: Metrics = read_json(results_file)
    else:
        res = compute_metric_stmt(output_file, result_dir, prompt_file, language, postprocessor)
    return LabelledMetrics(
        **res,
        model=model_short,
        task=args.task,
        language=language,
        template=template,
        postprocess=postprocessor.name,
    )


def print_metrics_table(args: EvaluateArgs, results: list[LabelledMetrics]):
    metrics = ["em", "es", "stop"]
    short_models = [model.split("/")[-1] for model in args.model]

    dataframe = pandas.DataFrame(results)
    grouped = pandas.pivot_table(
        dataframe, values=metrics, index=["model", "template"], columns=["language"]
    )

    # Calculate the mean across language columns for each metric and add it to the pivot table

    for metric in metrics:
        # Get the mean across all languages for this metric
        metric_values = grouped.xs(metric, axis=1, level=0)
        assert isinstance(metric_values, pandas.DataFrame)
        mean_values = metric_values.mean(axis=1).round(2)
        # Add the mean as a new column with language = 'Average'
        grouped[(metric, "Average")] = mean_values

    def key_function(x):
        print(x)
        return metrics.index(x)

    grouped = grouped.sort_index(
        axis=1, level=0, sort_remaining=False, key=lambda ind: ind.map(lambda v: metrics.index(v))
    )
    grouped = grouped.sort_index(
        axis=0,
        level=1,
        sort_remaining=False,
        key=lambda ind: ind.map(lambda v: args.template.index(v)),
    )
    grouped = grouped.sort_index(
        axis=0,
        level=0,
        sort_remaining=False,
        key=lambda ind: ind.map(lambda v: short_models.index(v)),
    )
    grouped = grouped.rename(
        columns={"em": "Exact Match %", "es": "Edit Similarity", "stop": "Stop %"}, level=0
    )

    #    If we want to sort first by language, then by metric type
    #    grouped = grouped.swaplevel(0, 1, axis=1)
    #    grouped = grouped.sort_index(axis=1, level=0)
    print(grouped)


def write_metrics_json(results: list[LabelledMetrics]):
    json_results = [
        {
            "model": result["model"].split("/")[-1],
            "language": result["language"],
            "template": result["template"],
            "postprocess": result["postprocess"],
            "exactMatch": result["em"],
            "editSimilarity": result["es"],
            "stop": result["stop"],
        }
        for result in results
    ]

    write_json(Path("web/public/metrics.json"), json_results, create_parents=True)


def write_samples(args: EvaluateArgs):
    manifest_path = Path("web/public/samples/manifest.json")
    write_json(manifest_path, {
        "models": [m.split("/")[-1] for m in args.model],
        "languages": args.language,
        "templates": args.template,
        "postprocessors": args.postprocess,
    }, create_parents=True)

    for language in args.language:
        prompt_file = get_prompt_path(args, language)

        with open(prompt_file, encoding="utf-8") as f:
            line_count = 0
            for line in f:
                line_count += 1

        random.seed(42)
        selected_line_nos = set(random.sample(range(line_count), 25))

        selected_task_ids = set()
        sample_inputs_file = Path("web/public/samples/_") / language / "inputs.jsonl"
        with write_jsonl(sample_inputs_file, create_parents=True) as writer:
            i = 0
            example: Example
            for example in read_jsonl(prompt_file):
                if i in selected_line_nos:
                    writer.append(example)
                    selected_task_ids.add(example["metadata"]["task_id"])
                i += 1

        def iterate_selected_tasks(path: Path):
            for data in read_jsonl(path):
                if data["task_id"] in selected_task_ids:
                    yield data

        for model in args.model:
            model_short = model.split("/")[-1]
            for template in args.template:
                sample_outputs_file = (
                    Path("web/public/samples") / model_short / language / template / "outputs.jsonl"
                )
                with write_jsonl(sample_outputs_file, create_parents=True) as writer:
                    output_file = get_output_path(args, model, language, template)
                    prediction: Prediction
                    for prediction in iterate_selected_tasks(output_file):
                        writer.append(
                            LabelledPrediction(
                                **prediction,
                                model=model,
                                task=args.task,
                                language=language,
                                template=template,
                            )
                        )

                for postprocess in args.postprocess:
                    result_dir = get_result_dir(args, model, language, template, postprocess)

                    results_file = result_dir / "detailed_results.jsonl"
                    results_map = {
                        result["task_id"]: result for result in iterate_selected_tasks(results_file)
                    }

                    sample_results_file = (
                        Path("web/public/samples")
                        / model_short
                        / language
                        / template
                        / postprocess
                        / "results.jsonl"
                    )
                    with write_jsonl(sample_results_file, create_parents=True) as writer:
                        prediction_file = result_dir / "prediction_truncated.jsonl"
                        for truncated in iterate_selected_tasks(prediction_file):
                            task_id = truncated["task_id"]
                            result = results_map[task_id]

                            writer.append(
                                LabelledResult(
                                    model=model,
                                    task=args.task,
                                    language=language,
                                    template=template,
                                    postprocess=postprocess,
                                    task_id=task_id,
                                    postprocessed=truncated["pred"],
                                    exactMatch=result["em"] == 1,
                                    editSimilarity=result["es"],
                                    stop=result["stop"],
                                )
                            )


def command(args: EvaluateArgs):
    os.makedirs(args.results_dir, exist_ok=True)

    results: list[LabelledMetrics] = []

    for model in args.model:
        for language in args.language:
            postprocessors: list[PostProcessor] = []
            for postprocessor_name in args.postprocess:
                try:
                    postprocessors.append(create_postprocessor(postprocessor_name, language))
                except ValueError:
                    raise ArgumentTypeError(f"unknown postprocessor name `{postprocessor_name}`")

            for template in args.template:
                for postprocessor in postprocessors:
                    result = evaluate(args, model, language, template, postprocessor)
                    if result:
                        results.append(result)

    if args.update_web:
        write_metrics_json(results)
        write_samples(args)

    print_metrics_table(args, results)
