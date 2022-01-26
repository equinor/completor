"""Completion."""

from __future__ import annotations

from typing import Union, overload

import numpy as np
import numpy.typing as npt
import pandas as pd

from completor.constants import Completion, SegmentCreationMethod
from completor.logger import logger
from completor.read_schedule import fix_compsegs, fix_welsegs
