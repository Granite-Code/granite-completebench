import { Link } from "react-router";
import {
  METRIC_DESCRIPTIONS,
  METRICS,
  MetricsStore,
} from "../utils/fetchMetrics";

interface MetricsTableProps {
  store: MetricsStore;
  postprocessor: string;
}

export function MetricsTable({ store, postprocessor }: MetricsTableProps) {
  console.log(postprocessor);
  return (
    <table>
      <colgroup>
        <col />
        <col />
      </colgroup>
      {METRICS.map((metric) => (
        <colgroup key={metric}>
          {store.languages.map((language) => (
            <col key={metric + "-" + language} />
          ))}
        </colgroup>
      ))}
      <thead>
        <tr>
          <th />
          <th />
          {Object.entries(METRIC_DESCRIPTIONS).map(([metric, description]) => (
            <th colSpan={store.languages.length} key={metric}>
              {description}
            </th>
          ))}
        </tr>
        <tr>
          <th>Model</th>
          <th>template</th>
          {METRICS.map((metric) =>
            store.languages.map((language) => (
              <th key={metric + "-" + language}>{language}</th>
            )),
          )}
        </tr>
      </thead>
      <tbody>
        {store.models.map((model) =>
          store.templates.map((template, i) => (
            <tr key={model + "-" + template} className={i == 0 ? "first" : ""}>
              {/* Row headers */}
              {i == 0 ? <th rowSpan={store.templates.length}>{model}</th> : ""}
              <th>{template}</th>
              {/* Row Values */}
              {METRICS.map((metric) =>
                store.languages.map((language) => (
                  <td key={metric + "-" + language}>
                    {language != "Average" ? (
                      <Link
                        to={`/samples?model=${model}&language=${language}&template=${template}&postprocessor=${postprocessor}`}
                      >
                        {store.getFormattedMetric(
                          {
                            model,
                            language,
                            template,
                            postprocess: postprocessor,
                          },
                          metric,
                        )}
                      </Link>
                    ) : (
                      store.getFormattedMetric(
                        {
                          model,
                          language,
                          template,
                          postprocess: postprocessor,
                        },
                        metric,
                      )
                    )}
                  </td>
                )),
              )}
            </tr>
          )),
        )}
      </tbody>
    </table>
  );
}
