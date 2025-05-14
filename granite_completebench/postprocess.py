from abc import ABC, abstractmethod
from functools import cache
from typing import ClassVar

from tree_sitter import Language, Parser

from .types import Example


@cache
def get_treesitter_language(lang: str):
    if lang == "python":
        import tree_sitter_python

        return Language(tree_sitter_python.language())
    elif lang == "csharp":
        import tree_sitter_c_sharp

        return Language(tree_sitter_c_sharp.language())
    elif lang == "java":
        import tree_sitter_java

        return Language(tree_sitter_java.language())
    elif lang == "typescript":
        import tree_sitter_typescript

        return Language(tree_sitter_typescript.language_typescript())
    elif lang == "tsx":
        import tree_sitter_typescript

        return Language(tree_sitter_typescript.language_tsx())
    else:
        raise RuntimeError(f"Unknown language {lang}")


class PostProcessor(ABC):
    name: ClassVar[str]

    def __init__(self, lang: str):
        self.lang = lang

        # Thead safety
        get_treesitter_language(lang)
        if lang == "typescript":
            get_treesitter_language("tsx")

    def get_parser(self, example: Example):
        lang = self.lang
        if self.lang == "typescript" and example["metadata"]["file"].endswith(".tsx"):
            lang = "tsx"
        return Parser(get_treesitter_language(lang))

    @abstractmethod
    def postprocess(self, example: Example, prediction: str) -> str:
        pass


class ChainedPostProcessor(PostProcessor):
    processor_classes: ClassVar[list[type[PostProcessor]]]

    def __init__(self, *args, **kwargs):
        self.processors = [c(*args, **kwargs) for c in self.processor_classes]

    def postprocess(self, example: Example, prediction: str) -> str:
        for processor in self.processors:
            prediction = processor.postprocess(example, prediction)

        return prediction


@cache
def _get_postprocessor_map():
    import granite_completebench.postprocessors

    postprocessor_map: dict[str, type[PostProcessor]] = {}

    def iterate_subclasses(cls: type[PostProcessor]):
        if cls not in (PostProcessor, ChainedPostProcessor):
            postprocessor_map[cls.name] = cls

        for c in cls.__subclasses__():
            iterate_subclasses(c)

    iterate_subclasses(PostProcessor)

    return postprocessor_map


def create_postprocessor(name: str, lang: str) -> PostProcessor:
    return _get_postprocessor_map()[name](lang)
