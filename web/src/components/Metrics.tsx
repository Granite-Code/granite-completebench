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
      <MetricsTable postprocessor={postprocessor} store={store} />
      <div id="explanations">
        <h2>Template</h2>
        <p>
          <b>no_snippets</b> No RAG snippets are included.
          <br />
          <b>comment</b> Snippets are part of the FIM prefix, commented out
          <br />
          <b>inside</b> Snippets are part of the FIM prefix, deliminated by
          &lt;filename&gt; or &lt;|file_sep|&gt;
          <br />
          <b>outside</b> Snippets are before the FIM template, deliminated by
          &lt;filename&gt; or &lt;|file_sep|&gt;
          <br />
        </p>
        <h2>Postprocess</h2>
        <p>
          <b>none</b> No postprocessing <br />
          <b>truncate_suffix</b> If the generated code matches the start of the
          suffix, truncate it. (One of Continue's postprocessing steps.)
          <br />
          <b>truncate_suffix_close</b> As with truncate_suffix, but
          additionally, if the suffix starts with a close character, or dedent,
          truncate the output at the end of the block.
          <br />
          <b>truncate_expression</b> Truncate the generated output at the end of
          a single expression. (CrossCodeEval behavior - does not test FIM
          completion well.)
        </p>
        <h2>Metrics</h2>
        <p>
          <b>Exact Match %</b> Percentage of cases where the output after
          postprocessing is identical to the original code. <br />
          <b>Edit Similarity</b> Average{" "}
          <a href="https://rapidfuzz.github.io/Levenshtein/levenshtein.html#ratio">
            normalized similarity
          </a>{" "}
          <br />
          <b>Stop %</b> Percentage of cases where the model stops generating
          before hitting the token limit, or whether postprocessing finds a
          place to cut the output short.
        </p>
      </div>
    </div>
  );
}
