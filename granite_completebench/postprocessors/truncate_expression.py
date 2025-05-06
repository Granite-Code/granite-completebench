from ..eval_utils import postprocess_code_lines
from ..postprocess import PostProcessor
from ..types import Example


class TruncateExpression(PostProcessor):
    name = "truncate_expression"

    def postprocess(self, example: Example, prediction: str) -> str:
        return postprocess_code_lines(
            example["prompt"], prediction, self.get_parser(example), self.lang
        )
