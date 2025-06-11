import { createContext, useContext, useEffect, useState } from "react";
import { BASE } from "../site";

interface Manifest {
  models: string[];
  languages: string[];
  templates: string[];
  postprocessors: string[];
}

const emptyManifest: Manifest = {
  models: [],
  languages: [],
  templates: [],
  postprocessors: [],
};

const SampleManifestContext = createContext<Manifest | undefined>(undefined);

export function SampleManifestProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [manifest, setManifest] = useState<Manifest>(emptyManifest);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadManifest() {
      try {
        const response = await fetch(BASE + "/samples/manifest.json");

        if (!response.ok) {
          throw new Error(`Failed to load manifest: ${response.statusText}`);
        }

        const data = await response.json();
        setManifest(data);
      } catch (err) {
        console.error("Error loading manifest:", err);
        setError(err instanceof Error ? err.message : "Failed to load options");
      }
    }

    loadManifest();
  }, []);

  if (error) {
    // You might want to handle this differently depending on your needs
    console.error(error);
  }

  return (
    <SampleManifestContext.Provider value={manifest}>
      {children}
    </SampleManifestContext.Provider>
  );
}

export function useSampleManifest() {
  const context = useContext(SampleManifestContext);
  if (context === undefined) {
    throw new Error(
      "useSampleManifest must be used within a SampleManifestProvider",
    );
  }
  return context;
}
