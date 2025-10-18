"""Deterministic arithmetic helpers for the meta-testing sample project."""

from __future__ import annotations


def add(lhs: int, rhs: int) -> int:
    """Return the sum of two integers."""

    return lhs + rhs


def subtract(lhs: int, rhs: int) -> int:
    """Return the difference between two integers."""

    return lhs - rhs


def multiply(lhs: int, rhs: int) -> int:
    """Return the product of two integers."""

    return lhs * rhs


def divide(lhs: int, rhs: int) -> float:
    """Return the quotient of two integers."""

    if rhs == 0:
        raise ZeroDivisionError("division by zero is undefined")

    return lhs / rhs
