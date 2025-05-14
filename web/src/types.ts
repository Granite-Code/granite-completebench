interface ExampleMetadata {
  task_id: string;
  repository: string;
  file: string;
  context_start_lineno: number;
  groundtruth_start_lineno: number;
  right_context_start_lineno: number;
}

interface CrossFileItem {
  retrieved_chunk: string;
  filename: string;
  score: number;
}

interface CrossFileContext {
  text: string;
  list: CrossFileItem[];
}

export interface Example {
  prompt: string;
  groundtruth: string;
  right_context: string;
  metadata: ExampleMetadata;
  crossfile_context: CrossFileContext;
}

export interface Prediction {
  task_id: string;
  templated: string;
  output: string;
  stop_reason: string;
}

export interface LabelledPrediction extends Prediction {
  model: string;
  task: string;
  language: string;
  template: string;
}

export interface LabelledResult {
  model: string;
  task: string;
  language: string;
  template: string;
  postprocess: string;
  task_id: string;
  postprocessed: string;
  exactMatch: boolean;
  editSimilarity: number;
  stop: boolean;
}

export interface Sample {
  input: Example;
  output: LabelledPrediction;
  result: LabelledResult;
}
