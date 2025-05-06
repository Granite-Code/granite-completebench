from ..types import Example
from ..postprocess import PostProcessor


class TruncateSuffix(PostProcessor):
    name = "truncate_suffix"

    def postprocess(self, example: Example, prediction: str) -> str:
        # This duplicates the handling in
        # continue/autocomplete/filtering/streamTransforms/charStream.ts:stopAtStartOf

        suffix = example["right_context"]
        sequence_length = 20
        if len(suffix) < sequence_length:
            return prediction

        targetPart = suffix.lstrip()[0 : int(sequence_length * 1.5)]

        for i in range(0, len(prediction) - sequence_length):
            if prediction[i : i + sequence_length] in targetPart:
                return prediction[0:i]

        return prediction
