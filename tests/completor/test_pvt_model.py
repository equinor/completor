"""Test functions for the Completor pvt_model module."""

from pathlib import Path

from completor import pvt_model  # type: ignore

_TESTDIR = Path(__file__).absolute().parent / "data"


def test_correlation_udq():
