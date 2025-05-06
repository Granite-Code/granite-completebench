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


class Metrics(TypedDict):
    em: float
    es: float
    stop: float
    id_em: float
    id_precision: float
    id_recall: float
    id_f1: float
    total: int


class LabelledMetrics(Metrics):
    model: str
    task: str
    language: str
    template: str
    postprocess: str


class LabelledPrediction(Prediction):
    model: str
    task: str
    language: str
    template: str


class LabelledResult(TypedDict):
    model: str
    task: str
    language: str
    template: str
    postprocess: str
    task_id: str
    postprocessed: str
    exactMatch: bool
    editSimilarity: float
    stop: bool
