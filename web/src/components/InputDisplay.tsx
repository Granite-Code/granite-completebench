import type { Sample } from "../types";

interface InputDisplayProperties {
  sample: Sample;
}

export default function InputDisplay({
  sample: { output },
}: InputDisplayProperties) {
  return (
    <div>
      <h1>{output.task_id}</h1>
      <pre>{output.templated}</pre>
    </div>
  );
}
