import { useEffect, useState } from "react";
import { useSearchParams } from "react-router";
import SampleDisplay from "./SampleDisplay";
import { Dropdown } from "./Dropdown";
import { fetchSamples } from "../utils/fetchSamples";
import type { Sample } from "../types";
import SampleSelector from "./SampleSelector";

interface Manifest {
  models: string[];
  languages: string[];
  templates: string[];
  postprocessors: string[];
}

// Default empty options to use before loading
const emptyOptions: string[] = [];

function validateSearchParams(
  searchParams: URLSearchParams,
  manifest: Manifest,
) {
  let newSearchParams: URLSearchParams | undefined;

  for (const [pluralKey, options] of Object.entries(manifest)) {
    const key = pluralKey.slice(0, -1);
    let value = searchParams.get(key) || "";
    if (!options.includes(value)) {
      value = options.length > 0 ? options[0] : "";
      if (newSearchParams === undefined)
        newSearchParams = new URLSearchParams(searchParams);
      newSearchParams.set(key, value);
    }
  }

  return newSearchParams ?? searchParams;
}

export function Samples() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [manifest, setManifest] = useState<Manifest>({
    models: emptyOptions,
    languages: emptyOptions,
    templates: emptyOptions,
    postprocessors: emptyOptions,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isInitialized, setIsInitialized] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [samples, setSamples] = useState<Sample[]>([]);
  const [current, setCurrent] = useState<number | undefined>();

  // Load manifest.json
  useEffect(() => {
    async function loadManifest() {
      try {
        const response = await fetch("/samples/manifest.json");

        if (!response.ok) {
          throw new Error(`Failed to load manifest: ${response.statusText}`);
        }

        const data = await response.json();
        setManifest(data);
        setIsLoading(false);
      } catch (err) {
        console.error("Error loading manifest:", err);
        setError(err instanceof Error ? err.message : "Failed to load options");
        setIsLoading(false);
      }
    }

    loadManifest();
  }, []);

  useEffect(() => {
    if (isLoading || isInitialized) return;

    setSearchParams((prev) => validateSearchParams(prev, manifest));
    setIsInitialized(true);
  }, [isLoading, isInitialized, manifest, searchParams]);

  useEffect(() => {
    if (!isInitialized) return;

    let validated = validateSearchParams(searchParams, manifest);
    const model = validated.get("model");
    const language = validated.get("language");
    const template = validated.get("template");
    const postprocessor = validated.get("postprocessor");
    if (!model || !language || !template || !postprocessor) return;

    const fetchData = async () => {
      try {
        const newSamples = await fetchSamples(
          model,
          language,
          template,
          postprocessor,
        );
        setSamples(newSamples);

        if (current === undefined || current >= samples.length) {
          setCurrent(0);
        }
      } catch (error) {
        console.log("Error fetching samples", error);
      }
    };

    fetchData();
  }, [isInitialized, searchParams]);

  if (!isInitialized || samples.length == 0 || current === undefined) {
    return <div>Loading options...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div>
      <div id="sampleNavigation">
        <span className="label">Model:&nbsp;</span>
        <Dropdown paramKey="model" options={manifest.models} />
        <span className="label">Language:&nbsp;</span>
        <Dropdown paramKey="language" options={manifest.languages} />
        <span className="label">Template:&nbsp;</span>
        <Dropdown paramKey="template" options={manifest.templates} />
        <span className="label">Postprocess:&nbsp;</span>
        <Dropdown paramKey="postprocessor" options={manifest.postprocessors} />
        <SampleSelector
          count={samples.length}
          current={current}
          setCurrent={setCurrent}
        />
      </div>
      <SampleDisplay sample={samples[current]} />
    </div>
  );
}
