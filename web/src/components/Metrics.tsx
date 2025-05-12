import { MetricsTable } from "./MetricsTable";
import { useSearchParams } from "react-router";

const TRUNCATE = ["none", "suffix", "suffix-close", "expression"];

export function Metrics() {
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedTruncate = searchParams.get("truncate") ?? TRUNCATE[0];

  return (
    <div id="metrics">
      <div id="truncateSelect">
        <span className="label">Truncate:&nbsp;</span>
        <select onChange={(e) => setSearchParams({ truncate: e.target.value })}>
          {TRUNCATE.map((truncate) => (
            <option
              key={truncate}
              value={truncate}
              selected={truncate === selectedTruncate}
            >
              {truncate}
            </option>
          ))}
        </select>
      </div>
      <MetricsTable truncate={selectedTruncate} />;
    </div>
  );
}
