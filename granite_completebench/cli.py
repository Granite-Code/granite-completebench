import argparse
from dataclasses import dataclass
from typing import Literal


@dataclass
class BaseArgs:
    command: str
    model: list[str]
    language: list[Literal["csharp", "python", "java", "typescript"]]
    task: str
    template: list[Literal["no_snippets", "inside", "outside", "comment"]]
    data_root_dir: str
    output_dir: str

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser):
        parser.add_argument(
            "--model", type=str, action="append", required=True, help="vLLM-supported model"
        )
        parser.add_argument(
            "--language",
            type=str,
            required=True,
            choices=["csharp", "python", "java", "typescript"],
            action="append",
        )
        parser.add_argument(
            "--task",
            type=str,
            required=True,
        )
        parser.add_argument(
            "--template",
            type=str,
            choices=["no_snippets", "inside", "outside", "comment"],
            action="append",
            required=True,
            help="template used for for the prompt and RAG snippets",
        )
        parser.add_argument(
            "--data-root-dir",
            type=str,
            default="data/",
            help="path to directory where data is organized in lang/task.jsonl format",
        )
        parser.add_argument(
            "--output-dir",
            type=str,
            default="./outputs",
            help="path to directory where to generation outputs are stored",
        )


@dataclass
class EvaluateArgs(BaseArgs):
    postprocess: list[str]
    results_dir: str
    update_web: bool

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser):
        super().add_arguments(parser)

        parser.add_argument(
            "--postprocess",
            type=str,
            action="append",
            help="none or the name of a postprocessor",
        )
        parser.add_argument(
            "--results-dir",
            type=str,
            default="./results",
            help="path to directory where to evaluation results are stored",
        )
        parser.add_argument(
            "--update-web", action="store_true", help="update data files for the website"
        )


@dataclass
class GenerateArgs(BaseArgs):
    temperature: float
    top_p: float
    generation_max_tokens: int

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser):
        super().add_arguments(parser)

        parser.add_argument("--temperature", type=float, default=0.2)
        parser.add_argument("--top_p", type=float, default=0.95)
        parser.add_argument(
            "--generation_max_tokens",
            type=int,
            default=128,
            help="maximum number of tokens to generate",
        )


@dataclass
class GenerateVllmArgs(GenerateArgs):
    tp_size: int
    model_max_tokens: int

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser):
        super().add_arguments(parser)

        parser.add_argument("--tp_size", type=int, default=1, help="tensor parallel size")
        parser.add_argument(
            "--model_max_tokens",
            type=int,
            default=16384,
            help="maximum number of tokens of the model",
        )


def main():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    generate_vllm_parser = subparsers.add_parser(
        "generate-vllm", help="Generate completions using vLLM"
    )
    GenerateArgs.add_arguments(generate_vllm_parser)

    evaluate_parser = subparsers.add_parser("evaluate", help="Evaluate generation results")
    EvaluateArgs.add_arguments(evaluate_parser)

    args = parser.parse_args()

    if args.command == "generate-vllm":
        try:
            from .generate_vllm import command as generate_vllm_command
        except ImportError as e:
            print(f"Error importing generate_vllm: {e}, try: `pip install -e '.[vllm]`")
            return 1
        generate_vllm_command(GenerateVllmArgs(**vars(args)))
    elif args.command == "evaluate":
        from .evaluate import command as evaluate_command

        try:
            evaluate_command(EvaluateArgs(**vars(args)))
        except argparse.ArgumentTypeError as e:
            print(f"{e}")
            return 1
    else:
        parser.print_help()
