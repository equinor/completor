"""Test functions for the Completor read_schedule module"""

from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd
from common import ReadSchedule

import completor.parse as fr
from completor import utils
from completor.read_schedule import fix_compsegs, fix_welsegs
