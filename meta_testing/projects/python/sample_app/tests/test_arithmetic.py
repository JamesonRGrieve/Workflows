"""Regression-friendly tests for the arithmetic helpers."""

from __future__ import annotations

import pytest

from sample_app import add, divide, multiply, subtract


def test_add():
    assert add(2, 3) == 5


def test_subtract():
    assert subtract(5, 2) == 3


def test_multiply():
    assert multiply(4, 6) == 24


@pytest.mark.parametrize(
    ("lhs", "rhs", "expected"),
    (
        (10, 2, 5.0),
        (7, -1, -7.0),
    ),
)
def test_divide(lhs: int, rhs: int, expected: float) -> None:
    assert divide(lhs, rhs) == expected


def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        divide(4, 0)
