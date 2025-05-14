import {
  type Sample,
  type Example,
  type LabelledPrediction,
  type LabelledResult,
} from "../types";

const parseJsonl = async (response: Response): Promise<any[]> => {
  const lines = await response.text().then((data) => data.split("\n"));
  if (lines[lines.length - 1] == "") {
    lines.pop();
  }
  return lines.map((line) => JSON.parse(line));
};

export async function fetchSamples(
  model: string,
  language: string,
  template: string,
  postprocessor: string,
): Promise<Sample[]> {
  const inputUrl = `/samples/_/${language}/inputs.jsonl`;
  const outputUrl = `/samples/${model}/${language}/${template}/outputs.jsonl`;
  const resultsUrl = `/samples/${model}/${language}/${template}/${postprocessor}/results.jsonl`;

  const [inputResponse, outputResponse, resultsResponse] = await Promise.all([
    fetch(inputUrl),
    fetch(outputUrl),
    fetch(resultsUrl),
  ]);

  if (!(inputResponse.ok && outputResponse.ok && resultsResponse.ok)) {
    throw new Error("Error fetching input/output/response arrays");
  }

  const inputArray: Example[] = await parseJsonl(inputResponse);
  const outputArray: LabelledPrediction[] = await parseJsonl(outputResponse);
  const resultsArray: LabelledResult[] = await parseJsonl(resultsResponse);

  if (
    inputArray.length != outputArray.length ||
    inputArray.length != resultsArray.length
  ) {
    throw new Error("Fetched arrays have unmatched lengths");
  }

  const inputMap = new Map(inputArray.map((v) => [v.metadata.task_id, v]));
  const outputMap = new Map(outputArray.map((v) => [v.task_id, v]));

  const returnValue: Sample[] = [];

  for (const result of resultsArray) {
    const input = inputMap.get(result.task_id);
    const output = outputMap.get(result.task_id);
    if (input === undefined || output === undefined) {
      throw new Error(`Can't find input and output for ${result.task_id}`);
    }

    returnValue.push({
      input,
      output,
      result,
    });
  }

  return returnValue;
}
