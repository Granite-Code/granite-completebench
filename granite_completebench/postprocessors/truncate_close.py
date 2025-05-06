from tree_sitter import Tree
from ..types import Example
from ..postprocess import PostProcessor


def check_for_errors(tree: Tree):
    cursor = tree.walk()
    has_error: bool = False

    def traverse():
        nonlocal has_error

        node = cursor.node
        if node and (node.is_error or node.is_missing):
            has_error = True

        if cursor.goto_first_child():
            traverse()
            while not has_error and cursor.goto_next_sibling():
                traverse()

            cursor.goto_parent()

    traverse()
    return has_error


def truncate_to_dedent(prefix, pred, suffix):
    last_prefix_line = prefix.split("\n")[-1]
    try:
        first_suffix_line = next(l for l in suffix.split("\n") if l.strip() != "")
    except StopIteration:
        first_suffix_line = None

    indent = len(last_prefix_line) - len(last_prefix_line.lstrip())
    next_indent = (
        len(first_suffix_line) - len(first_suffix_line.lstrip())
        if first_suffix_line is not None
        else 0
    )

    pos = 0
    for line in pred.split("\n"):
        if pos > 0 and line.strip() != "":
            line_indent = len(line) - len(line.lstrip())
            if line_indent <= next_indent and next_indent < indent:
                return pred[0:pos].rstrip()
        pos += len(line) + 1

    return pred


class TruncateClose(PostProcessor):
    name = "truncate_close"

    def truncate_to_dedent(self, example: Example, prediction: str) -> str:
        prefix = example["prompt"]
        suffix = example["right_context"]

        last_prefix_line = prefix.split("\n")[-1]
        try:
            first_suffix_line = next(l for l in suffix.split("\n") if l.strip() != "")
        except StopIteration:
            first_suffix_line = None

        indent = len(last_prefix_line) - len(last_prefix_line.lstrip())
        next_indent = (
            len(first_suffix_line) - len(first_suffix_line.lstrip())
            if first_suffix_line is not None
            else 0
        )

        pos = 0
        for line in prediction.split("\n"):
            if pos > 0 and line.strip() != "":
                line_indent = len(line) - len(line.lstrip())
                if line_indent <= next_indent and next_indent < indent:
                    return prediction[0:pos].rstrip()
            pos += len(line) + 1

        return prediction

    def truncate_to_close(self, example: Example, prediction: str):
        prefix = example["prompt"]
        suffix = example["right_context"]

        suffix_stripped = suffix.lstrip()
        if len(suffix_stripped) == 0:
            return prediction
        close_char = suffix_stripped[0]
        if close_char not in "]})":
            return prediction

        parser = self.get_parser(example)

        prefix_bytes = bytes(prefix, "utf8")
        pred_bytes = bytes(prediction, "utf8")
        close_bytes = bytes(close_char, "utf8")
        suffix_bytes = bytes(suffix, "utf8")
        suffix_close_offset = suffix_bytes.find(close_bytes)

        pred_close_offset = pred_bytes.find(close_bytes)
        while pred_close_offset >= 0:
            pred_selection = pred_bytes[0:pred_close_offset]
            contents = prefix_bytes + pred_selection + suffix_bytes[suffix_close_offset:]
            tree = parser.parse(contents)
            if not check_for_errors(tree):
                if pred_selection.endswith(suffix_bytes[0:suffix_close_offset]):
                    pred_selection = pred_selection[0:-suffix_close_offset]
                return pred_selection.decode("utf-8")

            pred_close_offset = pred_bytes.find(close_bytes, pred_close_offset + 1)

        return prediction

    def postprocess(self, example: Example, prediction: str) -> str:
        if self.lang == "python":
            prediction = self.truncate_to_dedent(example, prediction)
        else:
            prediction = self.truncate_to_close(example, prediction)

        return prediction
