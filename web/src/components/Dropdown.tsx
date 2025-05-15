import { useSearchParams } from "react-router";

export function Dropdown({
  paramKey,
  options,
}: {
  paramKey: string;
  options: string[];
}) {
  const [searchParams, setSearchParams] = useSearchParams();
  let validatedValue = searchParams.get(paramKey) ?? "";
  if (!options.includes(validatedValue)) {
    validatedValue = options[0];
  }

  return (
    <select
      value={validatedValue}
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
