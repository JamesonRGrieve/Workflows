import { sum, difference, product, quotient } from "./math";

export interface SampleComputation {
  label: string;
  value: number;
}

export function buildSampleReport(): SampleComputation[] {
  return [
    { label: "sum", value: sum(2, 3) },
    { label: "difference", value: difference(5, 2) },
    { label: "product", value: product(4, 6) },
    { label: "quotient", value: quotient(10, 2) }
  ];
}

console.log(JSON.stringify(buildSampleReport()));
