from typing import TypedDict


class ExampleMetadata(TypedDict):
    task_id: str
    repository: str
    file: str
    context_start_lineno: int
    groundtruth_start_lineno: int
    right_context_start_lineno: int


class CrossFileItem(TypedDict):
    retrieved_chunk: str
    filename: str
    score: float


class CrossFileContext(TypedDict):
    text: str
    list: list[CrossFileItem]


class Example(TypedDict):
    prompt: str
    groundtruth: str
    right_context: str
    metadata: ExampleMetadata
    crossfile_context: CrossFileContext


class Prediction(TypedDict):
    task_id: str
    templated: str
    output: str
    stop_reason: str
