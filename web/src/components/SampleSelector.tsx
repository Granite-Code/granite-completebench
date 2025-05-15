import type { Dispatch, SetStateAction } from "react";

interface SampleSelectorProperties {
  count: number;
  current: number;
  setCurrent: Dispatch<SetStateAction<number | undefined>>;
}

function SampleSelector({
  count,
  current,
  setCurrent,
}: SampleSelectorProperties) {
  return (
    <div id="sampleSelector">
      <button
        disabled={current === 0}
        onClick={() => setCurrent((prev) => Math.max(0, (prev ?? 0) - 1))}
      >
        &lt;
      </button>
      <span>{`${current + 1} / ${count}`}</span>
      <button
        disabled={current === count - 1}
        onClick={() =>
          setCurrent((prev) => Math.min(count - 1, (prev ?? 0) + 1))
        }
      >
        &gt;
      </button>
    </div>
  );
}

export default SampleSelector;
