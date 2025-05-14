import { useEffect, useState } from "react";
import { useSearchParams } from "react-router";
import SampleDisplay from "./SampleDisplay";

interface Manifest {
  models: string[];
  languages: string[];
  templates: string[];
  postprocessors: string[];
}

// Default empty options to use before loading
const emptyOptions: string[] = [];

// Helper function to get a validated option
const getValidatedOption = (
  searchParams: URLSearchParams,
  key: string,
  options: string[],
) => {
  if (options.length === 0) return "";

  const selectedValue = searchParams.get(key) || options[0];

  return options.indexOf(selectedValue) >= 0 ? selectedValue : options[0];
};

function Dropdown({
  paramKey,
  options,
}: {
  paramKey: string;
  options: string[];
}) {
  const [searchParams, setSearchParams] = useSearchParams();

  useEffect(() => {
    if (options.length === 0) return;

    const value = getValidatedOption(searchParams, paramKey, options);
    if (searchParams.get(paramKey) != value) {
      setSearchParams((prev) => {
        const newParams = new URLSearchParams(prev);
        newParams.set(paramKey, value);
        return newParams;
      });
    }
  }, [searchParams, options, paramKey, setSearchParams]);

  const value = getValidatedOption(searchParams, paramKey, options);

  return (
    <select
      value={value}
      name={paramKey}
      disabled={options.length === 0}
      onChange={(e) => {
        setSearchParams((prev) => {
          const newParams = new URLSearchParams(prev);
          newParams.set(paramKey, e.target.value);
          return newParams;
        });
      }}
    >
      {options.map((option) => (
        <option key={option} value={option}>
          {option}
        </option>
      ))}
    </select>
  );
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
  const [error, setError] = useState<string | null>(null);

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

  // Update URL params when manifest is loaded
  useEffect(() => {
    if (isLoading) return;

    const model = getValidatedOption(searchParams, "model", manifest.models);
    const language = getValidatedOption(
      searchParams,
      "language",
      manifest.languages,
    );
    const template = getValidatedOption(
      searchParams,
      "template",
      manifest.templates,
    );
    const postprocessor = getValidatedOption(
      searchParams,
      "postprocessor",
      manifest.postprocessors,
    );

    setSearchParams({
      model,
      language,
      template,
      postprocessor,
    });
  }, [manifest, isLoading, setSearchParams]);

  if (isLoading) {
    return <div>Loading options...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div>
      <Dropdown paramKey="model" options={manifest.models} />
      <Dropdown paramKey="language" options={manifest.languages} />
      <Dropdown paramKey="template" options={manifest.templates} />
      <Dropdown paramKey="postprocessor" options={manifest.postprocessors} />

      <SampleDisplay
        model={getValidatedOption(searchParams, "model", manifest.models)}
        language={getValidatedOption(
          searchParams,
          "language",
          manifest.languages,
        )}
        template={getValidatedOption(
          searchParams,
          "template",
          manifest.templates,
        )}
        postprocessor={getValidatedOption(
          searchParams,
          "postprocessor",
          manifest.postprocessors,
        )}
      />
    </div>
  );
}
