"""Functions for reading files."""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Literal, overload

import numpy as np

# Requires NumPy 1.20 or newer
import numpy.typing as npt
import pandas as pd

