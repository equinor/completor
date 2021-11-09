"""Defines a class for generating output files."""

from __future__ import annotations

import getpass
from datetime import datetime

import matplotlib  # type: ignore

from completor import prepare_outputs as po
from completor.completion import WellSchedule
from completor.create_wells import CreateWells
from completor.logger import logger
