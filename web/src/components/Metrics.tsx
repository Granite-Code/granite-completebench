import { useEffect, useState } from "react";
import { MetricsStore, fetchMetrics } from "../utils/fetchMetrics";
import { MetricsTable } from "./MetricsTable";
import { useSearchParams } from "react-router";

function validatedPostProcessor(
  searchParams: URLSearchParams,
  store: MetricsStore,
) {
  if (store.postprocessors.length == 0) {
    return "";
  }

  let selectedPostprocessor = searchParams.get("postprocessor");
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
  const [store, setStore] = useState<MetricsStore>(new MetricsStore());

  useEffect(() => {
    async function loadMetrics() {
      try {
        const newStore = await fetchMetrics();
        setStore(newStore);
      } catch (error) {
        console.log("Error loading metrics", error);
      }
    }

    loadMetrics();
  }, []);

  useEffect(() => {
    if (store.postprocessors.length == 0) {
      return;
    }

    let newPostProcessor = validatedPostProcessor(searchParams, store);
    if (newPostProcessor != searchParams.get("postprocessor")) {
      setSearchParams((params) => {
        let newParams = new URLSearchParams(params);
        newParams.set("postprocessor", newPostProcessor);
        return newParams;
      });
    }
  }, [store, searchParams, setSearchParams]);

  let postprocessor = validatedPostProcessor(searchParams, store);
  if (store.postprocessors.length == 0 || postprocessor === "")
    return <div>Loading...</div>;

  return (
    <div id="metrics">
      <div id="postprocessorSelect">
        <span className="label">Postprocess:&nbsp;</span>
        <select
          value={postprocessor}
          onChange={(e) => setSearchParams({ postprocessor: e.target.value })}
        >
          {store.postprocessors.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
      </div>
      <MetricsTable postprocessor={postprocessor} store={store} />;
    </div>
  );
}
