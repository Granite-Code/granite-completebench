import { BASE } from "../site";
import {
  type Sample,
  type Example,
  type LabelledPrediction,
  type LabelledResult,
  type PredictionWithTruncated,
} from "../types";

const parseJsonl = async (response: Response): Promise<any[]> => {
  const lines = await response.text().then((data) => data.split("\n"));
  if (lines[lines.length - 1] == "") {
    lines.pop();
  }
  return lines.map((line) => JSON.parse(line));
};

function commonPrefix(str1: string, str2: string) {
  for (let i = 0; i < str1.length && i < str2.length; i++) {
    if (str1[i] !== str2[i]) {
      return str1.slice(0, i);
    }
  }

  return str1.slice(0, str2.length);
}

function commonSuffix(str1: string, str2: string) {
  let i = str1.length - 1;
  let j = str2.length - 1;

  while (i >= 0 && j >= 0 && str1[i] === str2[j]) {
    i--;
    j--;
  }

  return str1.slice(i + 1);
}

function addTruncatedPrefixSuffix(input: Example, output: LabelledPrediction) {
  const match = /<fim_suffix>|<\|fim_suffix\|>/.exec(output.templated);
  if (match == null) {
    throw Error("Can't find fim_suffix in template");
  }

  const prefix = output.templated.slice(0, match.index);
  const suffix = output.templated.slice(match.index + match[0].length);

  return {
    ...output,
    truncatedPrefix: commonSuffix(input.prompt, prefix),
    truncatedSuffix: commonPrefix(input.right_context, suffix),
  } as PredictionWithTruncated;
}

export async function fetchSamples(
  model: string,
  language: string,
  template: string,
  postprocessor: string,
): Promise<Sample[]> {
  const inputUrl = `${BASE}/samples/_/${language}/inputs.jsonl`;
  const outputUrl = `${BASE}/samples/${model}/${language}/${template}/outputs.jsonl`;
  const resultsUrl = `${BASE}/samples/${model}/${language}/${template}/${postprocessor}/results.jsonl`;

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
      output: addTruncatedPrefixSuffix(input, output),
      result,
    });
  }

  // The samples for each task/language combination are consistent between different files,
  // but not sorted consistently; sort them so that when the user switches parameters,
  // they keep viewing the same sample.

  function compareTaskIds(a: Sample, b: Sample) {
    if (a.output.task_id === b.output.task_id) {
      return 0;
    } else {
      return a.output.task_id < b.output.task_id ? -1 : 1;
    }
  }

  returnValue.sort(compareTaskIds);

  return returnValue;
}
