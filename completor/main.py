"""Main module of Completor."""

from __future__ import annotations

import argparse
import logging
import os
import re
import time
from collections.abc import Callable, Mapping
from typing import overload

import numpy as np

import completor
from completor import parse
from completor.completion import WellSchedule
from completor.constants import Keywords
from completor.create_output import CreateOutput
from completor.create_wells import CreateWells
from completor.logger import handle_error_messages, logger
