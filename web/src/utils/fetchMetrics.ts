import { BASE } from "../site";

export const METRIC_DESCRIPTIONS: { [K in MetricName]: string } = {
  exactMatch: "Exact Match %",
  editSimilarity: "Edit Similarity",
  stop: "Stop %",
};
export const METRICS = Object.keys(METRIC_DESCRIPTIONS) as [MetricName];

interface MetricsKey {
  model: string;
  language: string;
  template: string;
  postprocess: string;
}

function makeKeyString(key: MetricsKey) {
  return `${key.model}-${key.language}-${key.template}-${key.postprocess}`;
}

interface MetricsValue extends MetricsKey {
  exactMatch: number;
  editSimilarity: number;
  stop: number;
}

type MetricName = Exclude<keyof MetricsValue, keyof MetricsKey>;

export class MetricsStore {
  private values: Map<string, MetricsValue>;

  models: string[] = [];
  languages: string[] = [];
  templates: string[] = [];
  postprocessors: string[] = [];

  constructor() {
    this.values = new Map();
  }

  async load() {
    const response = await fetch(BASE + "/metrics.json");
    const data = await response.json();

    const models = new Set<string>();
    const languages = new Set<string>();
    const templates = new Set<string>();
    const postprocessors = new Set<string>();

    for (const value of data) {
      models.add(value.model);
      languages.add(value.language);
      templates.add(value.template);
      postprocessors.add(value.postprocess);

      this.values.set(makeKeyString(value), value);
    }

    this.models = Array.from(models);
    this.languages = Array.from(languages);
    this.templates = Array.from(templates);
    this.postprocessors = Array.from(postprocessors);

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

export async function fetchMetrics() {
  const store = new MetricsStore();
  await store.load();
  return store;
}
