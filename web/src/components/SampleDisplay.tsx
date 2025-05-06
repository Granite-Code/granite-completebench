import InputDisplay from "./InputDisplay";
import ResultDisplay from "./ResultDisplay";
import { type Sample } from "../types";

interface SampleDisplayProperties {
  sample: Sample;
}

function SampleDisplay({ sample }: SampleDisplayProperties) {
  return (
    <div>
      <div id="sampleDisplay">
        <InputDisplay sample={sample} />
        <ResultDisplay sample={sample} />
      </div>
    </div>
  );
}

export default SampleDisplay;
