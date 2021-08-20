"""
This module tests that the roughness and ID for segments in the overburden
are described by the case file and not the input schedule file.
"""

import common

_TEST_FILE = "test.sch"


def test_perf(tmpdir):
    """
    Test case where the case and schedule files have differing overburden values.

    The roughness and ID of the overburden segment do not match between the files.
    """
    tmpdir.chdir()
