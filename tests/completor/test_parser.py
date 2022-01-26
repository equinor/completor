"""Test functions for the Completor parser module."""

from pathlib import Path

import numpy as np

from completor import parse  # type: ignore

_TESTDIR = Path(__file__).absolute().parent / "data"
