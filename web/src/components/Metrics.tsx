import { useEffect } from "react";
import { useSearchParams } from "react-router";
import { MetricsTable } from "./MetricsTable";
import { useMetrics } from "../context/Metrics";

function validatedPostProcessor(
  searchParams: URLSearchParams,
  store: ReturnType<typeof useMetrics>,
) {
  if (store.postprocessors.length == 0) {
    return "";
  }

  const selectedPostprocessor = searchParams.get("postprocessor");
  if (
    selectedPostprocessor === null ||
    store.postprocessors.indexOf(selectedPostprocessor) < 0
  ) {
    return store.postprocessors[0];
  } else {
    return selectedPostprocessor;
  }
}

export function Metrics() {
  const [searchParams, setSearchParams] = useSearchParams();
  const store = useMetrics();

  useEffect(() => {
    if (store.postprocessors.length == 0) {
      return;
    }

    const newPostProcessor = validatedPostProcessor(searchParams, store);
    if (newPostProcessor != searchParams.get("postprocessor")) {
      setSearchParams(
        (params) => {
          const newParams = new URLSearchParams(params);
          newParams.set("postprocessor", newPostProcessor);
          return newParams;
        },
        { replace: true },
      );
    }
  }, [store, searchParams, setSearchParams]);

  const postprocessor = validatedPostProcessor(searchParams, store);
  if (store.error) return <div>Error: {store.error}</div>;
  if (store.postprocessors.length == 0 || postprocessor === "")
    return <div>Loading...</div>;

  return (
    <div id="metrics">
      <div id="postprocessorSelect">
        <span className="label">Postprocess:&nbsp;</span>
        <select
          value={postprocessor}
          onChange={(e) =>
            setSearchParams(
              { postprocessor: e.target.value },
              { replace: true },
            )
          }
        >
          {store.postprocessors.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
      </div>
      <MetricsTable postprocessor={postprocessor} store={store} />
    </div>
  );
}
