import logging

import pytest

from completor.logger import logger


@pytest.fixture
def log_info():
    logger.setLevel(logging.INFO)


@pytest.fixture
def log_warning():
    logger.setLevel(logging.WARNING)


@pytest.fixture
def log_debug():
    logger.setLevel(logging.DEBUG)
