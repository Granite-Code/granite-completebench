import { Fragment, memo, useState } from "react";
import type { Sample } from "../types";

type SelectedTab = "source" | "snippets" | "prompt";

interface InputDisplayProperties {
  sample: Sample;
}

const InputDisplay = memo(function ({
  sample: { input, output },
}: InputDisplayProperties) {
  const [selectedTab, setSelectedTab] = useState<SelectedTab>("source");

  // Show the component
  return (
    <div id="inputDisplay">
      <div className="tab-bar">
        <span
          className={`tab ${selectedTab == "source" ? "active" : ""}`}
          onClick={() => setSelectedTab("source")}
        >
          Source
        </span>
        <span
          className={`tab ${selectedTab == "snippets" ? "active" : ""}`}
          onClick={() => setSelectedTab("snippets")}
        >
          Snippets
        </span>
        <span
          className={`tab ${selectedTab == "prompt" ? "active" : ""}`}
          onClick={() => setSelectedTab("prompt")}
        >
          Prompt
        </span>
      </div>
      <div>
        {selectedTab === "source" && (
          <pre className="body">
            {output.truncatedPrefix}
            <span style={{ color: "red" }}>{input.groundtruth}</span>
            {output.truncatedSuffix}
          </pre>
        )}
        {selectedTab === "snippets" && (
          <div className="body">
            {input.crossfile_context.list.map((item, i) => (
              <Fragment key={i}>
                <h2>{item.filename}</h2>
                <pre>{item.retrieved_chunk}</pre>
              </Fragment>
            ))}
          </div>
        )}
        {selectedTab === "prompt" && (
          <div id="promptWrapper" className="body">
            <pre id="prompt" className="body">
              {output.templated}
            </pre>
            <button
              id="promptCopy"
              onClick={() => {
                navigator.clipboard.writeText(output.templated);
              }}
            >
              Copy
            </button>
          </div>
        )}
      </div>
    </div>
  );
});

export default InputDisplay;
