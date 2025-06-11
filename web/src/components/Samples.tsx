import { useState, useEffect } from "react";
import { useSearchParams } from "react-router";
import SampleDisplay from "./SampleDisplay";
import { Dropdown } from "./Dropdown";
import { fetchSamples } from "../utils/fetchSamples";
import type { Sample } from "../types";
import SampleSelector from "./SampleSelector";
import { useSampleManifest } from "../context/SampleManifest";

function validateSearchParams(
  searchParams: URLSearchParams,
  manifest: ReturnType<typeof useSampleManifest>,
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
  const [isInitialized, setIsInitialized] = useState(false);
  const [samples, setSamples] = useState<Sample[]>([]);
  const [current, setCurrent] = useState<number | undefined>();
  const manifest = useSampleManifest();

  useEffect(() => {
    if (!manifest || isInitialized) return;

    setSearchParams(validateSearchParams(searchParams, manifest), {
      replace: true,
    });
    setIsInitialized(true);
  }, [manifest, isInitialized, searchParams, setSearchParams]);

  useEffect(() => {
    if (!isInitialized) return;

    const validated = validateSearchParams(searchParams, manifest);
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
  }, [isInitialized, searchParams, current, setCurrent, samples, manifest]);

  if (!isInitialized || samples.length == 0 || current === undefined) {
    return <div>Loading samples...</div>;
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
