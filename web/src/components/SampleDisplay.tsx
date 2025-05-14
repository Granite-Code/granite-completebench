import React, { useState, useEffect } from "react";
import InputDisplay from "./InputDisplay";
import ResultDisplay from "./ResultDisplay";
import { type Sample } from "../types";
import { fetchSamples } from "../utils/fetchSamples";

interface SampleDisplayProperties {
  model: string;
  language: string;
  template: string;
  postprocessor: string;
}

const SampleDisplay: React.FC<SampleDisplayProperties> = ({
  model,
  language,
  template,
  postprocessor,
}) => {
  const [samples, setSamples] = useState<Sample[]>([]);
  const [current, setCurrent] = useState<number | undefined>();

  useEffect(() => {
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
  }, [
    model,
    language,
    template,
    postprocessor,
    samples,
    setSamples,
    current,
    setCurrent,
  ]);

  if (samples.length == 0 || current === undefined) {
    return <div>Loading...</div>;
  }
  return (
    <div>
      <div className="controls">
        <span>&lt;</span>
        <span>{`${current + 1} / ${samples.length}`}</span>
        <span>&gt;</span>
      </div>
      <InputDisplay sample={samples[current]} />
      <ResultDisplay sample={samples[current]} />
    </div>
  );
};

export default SampleDisplay;
