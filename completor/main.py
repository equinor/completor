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

