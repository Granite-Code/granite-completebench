import { useEffect, useState } from "react";

interface MetricsKey {
  model: string;
  language: string;
  snippets: string;
  truncate: string;
}

function makeKeyString(key: MetricsKey) {
  return `${key.model}-${key.language}-${key.snippets}-${key.truncate}`;
}

interface MetricsValue extends MetricsKey {
  exactMatch: number;
  editSimilarity: number;
  stop: number;
}

type MetricName = Exclude<keyof MetricsValue, keyof MetricsKey>;

const METRIC_DESCRIPTIONS: { [K in MetricName]: string } = {
  exactMatch: "Exact Match %",
  editSimilarity: "Edit Similarity",
  stop: "Stop %",
};
const METRICS = Object.keys(METRIC_DESCRIPTIONS) as [MetricName];

class MetricsStore {
  private values: Map<string, MetricsValue>;

  models: string[] = [];
  languages: string[] = [];
  snippets: string[] = [];
  truncates: string[] = [];

  constructor() {
    this.values = new Map();
  }

  async load() {
    const response = await fetch("/metrics.json");
    const data = await response.json();

    const models = new Set<string>();
    const languages = new Set<string>();
    const snippets = new Set<string>();
    const truncates = new Set<string>();

    for (const value of data) {
      models.add(value.model);
      languages.add(value.language);
      snippets.add(value.snippets);
      truncates.add(value.truncate);

      this.values.set(makeKeyString(value), value);
    }

    this.models = Array.from(models);
    this.languages = Array.from(languages);
    this.snippets = Array.from(snippets);
    this.truncates = Array.from(truncates);

    this._addAverages();
  }

  getFormattedMetric(key: MetricsKey, metric: MetricName) {
    const keyString = makeKeyString(key);
    const value = this.values.get(keyString);
    if (value) {
      return value[metric].toFixed(2);
    }
    return "";
  }

  _addAverages() {
    const newStore = new Map(this.values);
    const counts = new Map<string, number>();
    for (const [_key, value] of this.values) {
      const averageKeyString = makeKeyString({
        ...value,
        language: "Average",
      });
      const averageValue = newStore.get(averageKeyString);
      if (averageValue) {
        for (const metric of METRICS) {
          averageValue[metric] += value[metric];
        }
        counts.set(averageKeyString, (counts.get(averageKeyString) ?? 0) + 1);
      } else {
        newStore.set(averageKeyString, { ...value });
        counts.set(averageKeyString, 1);
      }
    }
    for (const [key, count] of counts) {
      const value = newStore.get(key);
      if (value) {
        for (const metric of METRICS) {
          value[metric] /= count;
        }
      }
    }
    this.values = newStore;
    this.languages.push("Average");
  }
}

interface MetricsTableProps {
  truncate: string;
}

export function MetricsTable({ truncate }: MetricsTableProps) {
  const [store, setStore] = useState<MetricsStore>(new MetricsStore());

  useEffect(() => {
    const newStore = new MetricsStore();
    newStore.load().then(() => {
      setStore(newStore);
    });
  }, []);

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
          <th>Snippets</th>
          {METRICS.map((metric) =>
            store.languages.map((language) => (
              <th key={metric + "-" + language}>{language}</th>
            )),
          )}
        </tr>
      </thead>
      <tbody>
        {store.models.map((model) =>
          store.snippets.map((snippets, i) => (
            <tr key={model + "-" + snippets} className={i == 0 ? "first" : ""}>
              {/* Row headers */}
              {i == 0 ? <th rowSpan={store.snippets.length}>{model}</th> : ""}
              <th>{snippets}</th>
              {/* Row Values */}
              {METRICS.map((metric) =>
                store.languages.map((language) => (
                  <td key={metric + "-" + language}>
                    {store.getFormattedMetric(
                      { model, language, snippets, truncate },
                      metric,
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
