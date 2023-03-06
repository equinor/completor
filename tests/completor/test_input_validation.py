"""Test functions for input validation."""

from pathlib import Path

import pytest

from completor.input_validation import validate_minimum_segment_length
from completor.read_casefile import ReadCasefile
