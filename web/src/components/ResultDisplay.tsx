import type { Sample } from "../types";

interface ResultDisplayProperties {
  sample: Sample;
}

export default function ResultDisplay({
  sample: { output, result },
}: ResultDisplayProperties) {
  return (
    <div id="resultDisplay">
      <div id="sampleMetrics">
        <div>
          <span className="label">Exact Match:&nbsp;</span>
          {result.exactMatch ? "true" : "false"}
        </div>
        <div>
          <span className="label">Edit Similarity:&nbsp;</span>
          {result.editSimilarity}
        </div>
        <div>
          <span className="label">Stop:&nbsp;</span>
          {result.stop ? "true" : "false"}
        </div>
      </div>
      <pre className="body">
        {output.truncatedPrefix}
        <span style={{ color: "red" }}>{result.postprocessed}</span>
        {output.truncatedSuffix}
      </pre>
    </div>
  );
}
