from .truncate_close import TruncateClose
from .truncate_expression import TruncateExpression
from .truncate_suffix import TruncateSuffix
from ..postprocess import ChainedPostProcessor


class Nothing(ChainedPostProcessor):
    name = "none"
    processor_classes = []


class TruncateSuffixClose(ChainedPostProcessor):
    name = "truncate_suffix_close"
    processor_classes = [TruncateSuffix, TruncateClose]


__all__ = [
    "Nothing",
    "TruncateSuffix",
    "TruncateClose",
    "TruncateExpression",
    "TruncateSuffixClose",
]
