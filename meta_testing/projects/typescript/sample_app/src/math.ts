export function sum(lhs: number, rhs: number): number {
  return lhs + rhs;
}

export function difference(lhs: number, rhs: number): number {
  return lhs - rhs;
}

export function product(lhs: number, rhs: number): number {
  return lhs * rhs;
}

export function quotient(lhs: number, rhs: number): number {
  if (rhs === 0) {
    throw new Error("Division by zero is undefined");
  }

  return lhs / rhs;
}
