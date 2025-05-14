import type { Sample } from "../types";

interface ResultDisplayProperties {
  sample: Sample;
}

export default function ResultDisplay({
  sample: { output, result },
}: ResultDisplayProperties) {
  return (
    <div>
      <h1>{output.task_id}</h1>
      <pre>{result.postprocessed}</pre>
    </div>
  );
}
