from __future__ import annotations

import json
import logging
import sys
import time
from functools import wraps
from pathlib import Path


def getLogger(module_name="completor"):
    logger = logging.getLogger(module_name)
