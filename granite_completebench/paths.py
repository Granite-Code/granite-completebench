from pathlib import Path

from .cli import BaseArgs, EvaluateArgs


def model_short(model):
    return model.split("/")[-1]


def get_prompt_path(args: BaseArgs, language):
    return Path(args.data_root_dir) / language / f"{args.task}.jsonl"


def get_output_path(
    args: BaseArgs, model: str, language: str, snippet_type: str, create_dir: bool = False
):
    path = Path(args.output_dir) / model_short(model) / language / snippet_type / "prediction.jsonl"
    if create_dir:
        path.parent.mkdir(parents=True, exist_ok=True)

    return path


def get_result_dir(
    args: EvaluateArgs,
    model: str,
    language: str,
    snippet_type: str,
    truncate: str,
    create_dir: bool = False,
):
    path = Path(args.results_dir) / model_short(model) / language / snippet_type / truncate
    if create_dir:
        path.mkdir(parents=True, exist_ok=True)

    return path
