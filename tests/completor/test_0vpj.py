"""Both GP and OA types of annuli should block flow from the reservoir
to the devicelayer or annulus layer in 0 VPJ intervals. The 0 VPJ option should
also work both for cells-, fixed-, user- and welsegs type of segmentation methods."""

from pathlib import Path

from tests import utils_for_tests

_TESTDIR = Path(__file__).absolute().parent / "data"
_TEST_FILE = "test.sch"


SCHEDULE = """
WELSPECS
A1  FIELD  1  1  2000  OIL  1*  SHUT  YES  1* /
/

COMPDAT
A1  1  1  1  1  OPEN  0  10  0.2  2  0  1*  1*  1* /
A1  1  1  2  2  OPEN  0  10  0.2  2  0  1*  1*  1* /
A1  1  1  3  3  OPEN  0  10  0.2  2  0  1*  1*  1* /
A1  1  1  4  4  OPEN  0  10  0.2  2  0  1*  1*  1* /
A1  1  1  5  5  OPEN  0  10  0.2  2  0  1*  1*  1* /
A1  1  1  6  6  OPEN  0  10  0.2  2  0  1*  1*  1* /
A1  1  1  7  7  OPEN  0  10  0.2  2  0  1*  1*  1* /
A1  1  1  8  8  OPEN  0  10  0.2  2  0  1*  1*  1* /
A1  1  1  9  9  OPEN  0  10  0.2  2  0  1*  1*  1* /
A1  1  1 10 10  OPEN  0  10  0.2  2  0  1*  1*  1* /
/

WELSEGS
A1  2000  2000  1*  ABS  1*  1* /
2  2  1  1  2010  2010  0.2  1.00E-4 /
3  3  1  2  2020  2020  0.2  1.00E-4 /
4  4  1  3  2030  2030  0.2  1.00E-4 /
5  5  1  4  2040  2040  0.2  1.00E-4 /
6  6  1  5  2050  2050  0.2  1.00E-4 /
7  7  1  6  2060  2060  0.2  1.00E-4 /
8  8  1  7  2070  2070  0.2  1.00E-4 /
9  9  1  8  2080  2080  0.2  1.00E-4 /
10 10 1  9  2090  2090  0.2  1.00E-4 /
11 11 1 10  2100  2100  0.2  1.00E-4 /
/

COMPSEGS
A1 /
1  1  1  1  2000  2010  /
1  1  2  1  2010  2020  /
1  1  3  1  2020  2030  /
1  1  4  1  2030  2040  /
1  1  5  1  2040  2050  /
1  1  6  1  2050  2060  /
1  1  7  1  2060  2070  /
1  1  8  1  2070  2080  /
1  1  9  1  2080  2090  /
1  1 10  1  2090  2100  /
/
"""

CASE_GP_CELLS = """
-- No completion interval in lower half of the well
COMPLETION
A1 1    0  2000  0.15  0.216  1.5E-5  GP  0  ICD  1
A1 1 2000  2010  0.15  0.216  1.5E-5  GP  1  ICD  1
A1 1 2010  2020  0.15  0.216  1.5E-5  GP  1  ICD  1
A1 1 2020  2030  0.15  0.216  1.5E-5  GP  1  ICD  1
A1 1 2030  2040  0.15  0.216  1.5E-5  GP  1  ICD  1
A1 1 2040  2050  0.15  0.216  1.5E-5  GP  1  ICD  1
A1 1 2050  2060  0.15  0.216  1.5E-5  GP  0  ICD  1
A1 1 2060  2070  0.15  0.216  1.5E-5  GP  0  ICD  1
A1 1 2070  2080  0.15  0.216  1.5E-5  GP  0  ICD  1
A1 1 2080  2090  0.15  0.216  1.5E-5  GP  0  ICD  1
A1 1 2090  2100  0.15  0.216  1.5E-5  GP  0  ICD  1
A1 1 2100 99999  0.15  0.216  1.5E-5  GP  0  ICD  1
/

SEGMENTLENGTH
  0
/

USE_STRICT
  FALSE
/

WSEGSICD
1              0.001     1000        1           0.1
/
"""

CASE_OA_CELLS = """
-- No completion interval in lower half of the well
COMPLETION
A1 1    0  2000  0.15  0.216  1.5E-5  OA  0  ICD  1
A1 1 2000  2010  0.15  0.216  1.5E-5  OA  1  ICD  1
A1 1 2010  2020  0.15  0.216  1.5E-5  OA  1  ICD  1
A1 1 2020  2030  0.15  0.216  1.5E-5  OA  1  ICD  1
A1 1 2030  2040  0.15  0.216  1.5E-5  OA  1  ICD  1
A1 1 2040  2050  0.15  0.216  1.5E-5  OA  1  ICD  1
A1 1 2050  2060  0.15  0.216  1.5E-5  OA  0  ICD  1
A1 1 2060  2070  0.15  0.216  1.5E-5  OA  0  ICD  1
A1 1 2070  2080  0.15  0.216  1.5E-5  OA  0  ICD  1
A1 1 2080  2090  0.15  0.216  1.5E-5  OA  0  ICD  1
A1 1 2090  2100  0.15  0.216  1.5E-5  OA  0  ICD  1
A1 1 2100 99999  0.15  0.216  1.5E-5  OA  0  ICD  1
/

SEGMENTLENGTH
  0
/

USE_STRICT
  FALSE
/

WSEGSICD
1              0.001     1000        1           0.1
/
"""

CASE_GP_USER = """
-- No completion interval in lower half of the well
COMPLETION
A1 1    0  2000  0.15  0.216  1.5E-5  GP  0  ICD  1
A1 1 2000  2010  0.15  0.216  1.5E-5  GP  1  ICD  1
A1 1 2010  2040  0.15  0.216  1.5E-5  GP  1  ICD  1
A1 1 2040  2050  0.15  0.216  1.5E-5  GP  1  ICD  1
A1 1 2050  2060  0.15  0.216  1.5E-5  GP  0  ICD  1
A1 1 2060  2090  0.15  0.216  1.5E-5  GP  0  ICD  1
A1 1 2090  2100  0.15  0.216  1.5E-5  GP  0  ICD  1
A1 1 2100 99999  0.15  0.216  1.5E-5  GP  0  ICD  1
/

SEGMENTLENGTH
 -1
/

USE_STRICT
  FALSE
/

WSEGSICD
1              0.001     1000        1           0.1
/
"""


CASE_GP_ONELINER = """
-- No completion interval in lower half of the well
COMPLETION
A1 1    0 99999  0.15  0.216  1.5E-5  GP  1  ICD  1
/

SEGMENTLENGTH
 -1
/

USE_STRICT
  FALSE
/

WSEGSICD
1              0.001     1000        1           0.1
/
"""

CASE_OA_ONELINER = """
-- No completion interval in lower half of the well
COMPLETION
A1 1    0 99999  0.15  0.216  1.5E-5  OA  1  ICD  1
/

SEGMENTLENGTH
 -1
/

USE_STRICT
  FALSE
/

WSEGSICD
1              0.001     1000        1           0.1
/
"""

CASE_GP_USER_TOP_OVERLAP = """
-- No completion interval in lower half of the well
COMPLETION
A1 1    0  2014  0.15  0.216  1.5E-5  GP  0  ICD  1
A1 1 2014  2040  0.15  0.216  1.5E-5  GP  1  ICD  1
A1 1 2040  2050  0.15  0.216  1.5E-5  GP  1  ICD  1
A1 1 2050  2060  0.15  0.216  1.5E-5  GP  0  ICD  1
A1 1 2060  2090  0.15  0.216  1.5E-5  GP  0  ICD  1
A1 1 2090  2100  0.15  0.216  1.5E-5  GP  0  ICD  1
A1 1 2100 99999  0.15  0.216  1.5E-5  GP  0  ICD  1
/

SEGMENTLENGTH
 -1
/

USE_STRICT
  FALSE
/

WSEGSICD
1              0.001     1000        1           0.1
/

JOINTLENGTH
10
/
"""

CASE_GP_USER_BOTTOM_OVERLAP = """
-- No completion interval in lower half of the well
COMPLETION
A1 1    0  2010  0.15  0.216  1.5E-5  GP  0  ICD  1
A1 1 2010  2040  0.15  0.216  1.5E-5  GP  1  ICD  1
A1 1 2040  2050  0.15  0.216  1.5E-5  GP  1  ICD  1
A1 1 2050  2060  0.15  0.216  1.5E-5  GP  0  ICD  1
A1 1 2060  2086  0.15  0.216  1.5E-5  GP  1  ICD  1
A1 1 2086 99999  0.15  0.216  1.5E-5  GP  0  ICD  1
/

SEGMENTLENGTH
 -1
/

USE_STRICT
  FALSE
/

WSEGSICD
1              0.001     1000        1           0.1
/

JOINTLENGTH
10
/
"""

CASE_GP_USER_1VPJ = """
-- No completion interval in lower half of the well
COMPLETION
A1 1    0  2000  0.15  0.216  1.5E-5  GP  0  ICD  1
A1 1 2000  2010  0.15  0.216  1.5E-5  GP  1  ICD  1
A1 1 2010  2040  0.15  0.216  1.5E-5  GP  1  ICD  1
A1 1 2040  2050  0.15  0.216  1.5E-5  GP  1  ICD  1
A1 1 2050  2060  0.15  0.216  1.5E-5  GP  0  ICD  1
A1 1 2060  2090  0.15  0.216  1.5E-5  GP  1  ICD  1
A1 1 2090  2100  0.15  0.216  1.5E-5  GP  0  ICD  1
A1 1 2100 99999  0.15  0.216  1.5E-5  GP  0  ICD  1
/

SEGMENTLENGTH
 -1
/

USE_STRICT
  FALSE
/

WSEGSICD
1              0.001     1000        1           0.1
/

JOINTLENGTH
10
/
"""

CASE_GP_USER_0VPJ = """
-- No completion interval in lower half of the well
COMPLETION
A1 1    0  2000  0.15  0.216  1.5E-5  GP  0  ICD  1
A1 1 2000  2010  0.15  0.216  1.5E-5  GP  1  ICD  1
A1 1 2010  2040  0.15  0.216  1.5E-5  GP  0  ICD  1
A1 1 2040  2050  0.15  0.216  1.5E-5  GP  1  ICD  1
A1 1 2050  2060  0.15  0.216  1.5E-5  GP  0  ICD  1
A1 1 2060  2090  0.15  0.216  1.5E-5  GP  0  ICD  1
A1 1 2090  2100  0.15  0.216  1.5E-5  GP  0  ICD  1
A1 1 2100 99999  0.15  0.216  1.5E-5  GP  0  ICD  1
/

SEGMENTLENGTH
 -1
/

USE_STRICT
  FALSE
/

WSEGSICD
1              0.001     1000        1           0.1
/

JOINTLENGTH
10
/
"""

CASE_OA_USER = """
-- No completion interval in lower half of the well
COMPLETION
A1 1    0  2000  0.15  0.216  1.5E-5  OA  0  ICD  1
A1 1 2000  2010  0.15  0.216  1.5E-5  OA  1  ICD  1
A1 1 2010  2040  0.15  0.216  1.5E-5  OA  1  ICD  1
A1 1 2040  2050  0.15  0.216  1.5E-5  OA  1  ICD  1
A1 1 2050  2060  0.15  0.216  1.5E-5  OA  0  ICD  1
A1 1 2060  2090  0.15  0.216  1.5E-5  OA  0  ICD  1
A1 1 2090  2100  0.15  0.216  1.5E-5  OA  0  ICD  1
A1 1 2100 99999  0.15  0.216  1.5E-5  OA  0  ICD  1
/

SEGMENTLENGTH
 -1
/

USE_STRICT
  FALSE
/

WSEGSICD
1              0.001     1000        1           0.1
/
"""

CASE_OA_USER_TOP_OVERLAP = """
-- No completion interval in lower half of the well
COMPLETION
A1 1    0  2014  0.15  0.216  1.5E-5  GP  0  ICD  1
A1 1 2014  2040  0.15  0.216  1.5E-5  OA  1  ICD  1
A1 1 2040  2050  0.15  0.216  1.5E-5  OA  1  ICD  1
A1 1 2050  2060  0.15  0.216  1.5E-5  OA  0  ICD  1
A1 1 2060  2090  0.15  0.216  1.5E-5  OA  0  ICD  1
A1 1 2090  2100  0.15  0.216  1.5E-5  OA  1  ICD  1
A1 1 2100 99999  0.15  0.216  1.5E-5  GP  0  ICD  1
/

SEGMENTLENGTH
 -1
/

USE_STRICT
  FALSE
/

WSEGSICD
1              0.001     1000        1           0.1
/

JOINTLENGTH
10
/
"""

CASE_OA_USER_BOTTOM_OVERLAP = """
COMPLETION
A1 1    0  2000  0.15  0.216  1.5E-5  GP  0  ICD  1
A1 1 2000  2040  0.15  0.216  1.5E-5  OA  1  ICD  1
A1 1 2040  2050  0.15  0.216  1.5E-5  OA  1  ICD  1
A1 1 2050  2060  0.15  0.216  1.5E-5  OA  0  ICD  1
A1 1 2060  2086  0.15  0.216  1.5E-5  OA  1  ICD  1
A1 1 2086 99999  0.15  0.216  1.5E-5  GP  0  ICD  1
/

SEGMENTLENGTH
 -1
/

USE_STRICT
  FALSE
/

WSEGSICD
1              0.001     1000        1           0.1
/

JOINTLENGTH
10
/
"""

CASE_OA_USER_1VPJ = """
-- No completion interval in lower half of the well
COMPLETION
A1 1    0  2000  0.15  0.216  1.5E-5  OA  0  ICD  1
A1 1 2000  2010  0.15  0.216  1.5E-5  OA  1  ICD  1
A1 1 2010  2040  0.15  0.216  1.5E-5  OA  1  ICD  1
A1 1 2040  2050  0.15  0.216  1.5E-5  OA  1  ICD  1
A1 1 2050  2060  0.15  0.216  1.5E-5  OA  0  ICD  1
A1 1 2060  2090  0.15  0.216  1.5E-5  OA  1  ICD  1
A1 1 2090  2100  0.15  0.216  1.5E-5  OA  0  ICD  1
A1 1 2100 99999  0.15  0.216  1.5E-5  OA  0  ICD  1
/

SEGMENTLENGTH
 -1
/

USE_STRICT
  FALSE
/

WSEGSICD
1              0.001     1000        1           0.1
/

JOINTLENGTH
10
/
"""


CASE_OA_USER_1VPJ_PA = """
-- 1 VPJ interval in no completion Section in lower half of the well
COMPLETION
A1 1    0  2000  0.15  0.216  1.5E-5  OA  0  ICD  1
A1 1 2000  2010  0.15  0.216  1.5E-5  OA  1  ICD  1
A1 1 2010  2040  0.15  0.216  1.5E-5  OA  1  ICD  1
A1 1 2040  2050  0.15  0.216  1.5E-5  OA  1  ICD  1
A1 1 2050  2060  0.15  0.216  1.5E-5  OA  0  ICD  1
A1 1 2060  2060  0.15  0.216  1.5E-5  PA  0  ICD  1
A1 1 2060  2090  0.15  0.216  1.5E-5  OA  1  ICD  1
A1 1 2090  2100  0.15  0.216  1.5E-5  OA  0  ICD  1
A1 1 2100 99999  0.15  0.216  1.5E-5  OA  0  ICD  1
/

SEGMENTLENGTH
 -1
/

USE_STRICT
  FALSE
/

WSEGSICD
1              0.001     1000        1           0.1
/

JOINTLENGTH
10
/
"""

CASE_OA_USER_1VPJ = """
-- No completion interval in lower half of the well
COMPLETION
A1 1    0  2000  0.15  0.216  1.5E-5  OA  0  ICD  1
A1 1 2000  2010  0.15  0.216  1.5E-5  OA  1  ICD  1
A1 1 2010  2040  0.15  0.216  1.5E-5  OA  1  ICD  1
A1 1 2040  2050  0.15  0.216  1.5E-5  OA  1  ICD  1
A1 1 2050  2060  0.15  0.216  1.5E-5  OA  0  ICD  1
A1 1 2060  2090  0.15  0.216  1.5E-5  OA  1  ICD  1
A1 1 2090  2100  0.15  0.216  1.5E-5  OA  0  ICD  1
A1 1 2100 99999  0.15  0.216  1.5E-5  OA  0  ICD  1
/

SEGMENTLENGTH
 -1
/

USE_STRICT
  FALSE
/

WSEGSICD
1              0.001     1000        1           0.1
/

JOINTLENGTH
10
/
"""


CASE_OA_USER_USER = """
-- No completion interval in lower half of the well
COMPLETION
A1 1    0  2000  0.15  0.216  1.5E-5  OA  0  ICD  1
A1 1 2000  2010  0.15  0.216  1.5E-5  OA  1  ICD  1
A1 1 2010  2040  0.15  0.216  1.5E-5  OA  1  ICD  1
A1 1 2040  2050  0.15  0.216  1.5E-5  OA  1  ICD  1
A1 1 2050  2060  0.15  0.216  1.5E-5  OA  0  ICD  1
A1 1 2060  2090  0.15  0.216  1.5E-5  OA  1  ICD  1
A1 1 2090  2100  0.15  0.216  1.5E-5  OA  0  ICD  1
A1 1 2100 99999  0.15  0.216  1.5E-5  OA  0  ICD  1
/

SEGMENTLENGTH
 USER
/

USE_STRICT
  FALSE
/

WSEGSICD
1              0.001     1000        1           0.1
/

JOINTLENGTH
10
/
"""

CASE_OA_USER_0VPJ = """
-- No completion interval in lower half of the well
COMPLETION
A1 1    0  2000  0.15  0.216  1.5E-5  OA  0  ICD  1
A1 1 2000  2010  0.15  0.216  1.5E-5  OA  1  ICD  1
A1 1 2010  2040  0.15  0.216  1.5E-5  OA  0  ICD  1
A1 1 2040  2050  0.15  0.216  1.5E-5  OA  1  ICD  1
A1 1 2050  2060  0.15  0.216  1.5E-5  OA  0  ICD  1
A1 1 2060  2090  0.15  0.216  1.5E-5  OA  0  ICD  1
A1 1 2090  2100  0.15  0.216  1.5E-5  OA  0  ICD  1
A1 1 2100 99999  0.15  0.216  1.5E-5  OA  0  ICD  1
/

SEGMENTLENGTH
 -1
/

USE_STRICT
  FALSE
/

WSEGSICD
1              0.001     1000        1           0.1
/

JOINTLENGTH
10
/
"""


def test_gp_cells(tmpdir):
    """Test case with cells based segmentation and gravel packed annulus."""
    tmpdir.chdir()
    case_file = CASE_GP_CELLS
    true_file = Path(_TESTDIR / "gp_cells.true")
    utils_for_tests.open_files_run_create(case_file, SCHEDULE, _TEST_FILE)
    utils_for_tests.assert_results(true_file, _TEST_FILE)


def test_oa_cells(tmpdir):
    """Test case with cells based segmentation and open annulus."""
    tmpdir.chdir()
    case_file = CASE_OA_CELLS
    true_file = Path(_TESTDIR / "oa_cells.true")
    utils_for_tests.open_files_run_create(case_file, SCHEDULE, _TEST_FILE)
    utils_for_tests.assert_results(true_file, _TEST_FILE)


def test_gp_user(tmpdir):
    """Test case with user defined segmentation and gravel packed annulus."""
    tmpdir.chdir()
    case_file = CASE_GP_USER
    true_file = Path(_TESTDIR / "gp_user.true")
    utils_for_tests.open_files_run_create(case_file, SCHEDULE, _TEST_FILE)
    utils_for_tests.assert_results(true_file, _TEST_FILE)


def test_gp_user_top_overlap(tmpdir):
    """Test case with user defined segmentation and gravel packed annulus.

    The top 0 VPJ user specified interval (0 - x) overlaps with the reservoir.
    """
    tmpdir.chdir()
    case_file = CASE_GP_USER_TOP_OVERLAP
    true_file = Path(_TESTDIR / "gp_user_top_overlap.true")
    utils_for_tests.open_files_run_create(case_file, SCHEDULE, _TEST_FILE)
    utils_for_tests.assert_results(true_file, _TEST_FILE)


def test_gp_user_bottom_overlap(tmpdir):
    """Test case with user defined segmentation and gravel packed annulus.

    The bottom 0 VPJ user specified interval (y - 99999) overlaps with the reservoir.
    """
    tmpdir.chdir()
    case_file = CASE_GP_USER_BOTTOM_OVERLAP
    true_file = Path(_TESTDIR / "gp_user_bottom_overlap.true")
    utils_for_tests.open_files_run_create(case_file, SCHEDULE, _TEST_FILE)
    utils_for_tests.assert_results(true_file, _TEST_FILE)


def test_gp_user_1vpj(tmpdir):
    """Test case with user-defined segmentation,
    gravel packed annulus and a multi-segment 1 vpj part in the lower 0 vpj Section.
    """
    tmpdir.chdir()
    case_file = CASE_GP_USER_1VPJ
    true_file = Path(_TESTDIR / "gp_user_1vpj.true")
    utils_for_tests.open_files_run_create(case_file, SCHEDULE, _TEST_FILE)
    utils_for_tests.assert_results(true_file, _TEST_FILE)


def test_gp_user_0vpj(tmpdir):
    """Test case with user-defined segmentation,
    gravel packed annulus and a multi-segment 0 vpj part in the upper 1 vpj Section.
    """
    tmpdir.chdir()
    case_file = CASE_GP_USER_0VPJ
    true_file = Path(_TESTDIR / "gp_user_0vpj.true")
    utils_for_tests.open_files_run_create(case_file, SCHEDULE, _TEST_FILE)
    utils_for_tests.assert_results(true_file, _TEST_FILE)


def test_gp_oneliner(tmpdir):
    """Test case with user-defined segmentation, gravel packed annulus given in one line, i.e. one segment.

    Include 0-x and y -99999.
    """
    tmpdir.chdir()
    print(tmpdir)
    case_file = CASE_GP_ONELINER
    true_file = Path(_TESTDIR / "gp_user_oneliner.true")
    utils_for_tests.open_files_run_create(case_file, SCHEDULE, _TEST_FILE)
    utils_for_tests.assert_results(true_file, _TEST_FILE)


def test_oa_user(tmpdir):
    """Test case with user defined segmentation and open annulus."""
    tmpdir.chdir()
    case_file = CASE_OA_USER
    true_file = Path(_TESTDIR / "oa_user.true")
    utils_for_tests.open_files_run_create(case_file, SCHEDULE, _TEST_FILE)
    utils_for_tests.assert_results(true_file, _TEST_FILE)


def test_oa_user_top_overlap(tmpdir):
    """Test case with user defined segmentation and open annulus.

    Overlapping top user specified interval with reservoir.
    """
    tmpdir.chdir()
    case_file = CASE_OA_USER_TOP_OVERLAP
    true_file = Path(_TESTDIR / "oa_user_top_overlap.true")
    utils_for_tests.open_files_run_create(case_file, SCHEDULE, _TEST_FILE)
    utils_for_tests.assert_results(true_file, _TEST_FILE)


def test_oa_user_bottom_overlap(tmpdir):
    """Test case with user defined segmentation and open annulus.

    Overlapping bottom user specified interval with reservoir.
    """
    tmpdir.chdir()
    case_file = CASE_OA_USER_BOTTOM_OVERLAP
    true_file = Path(_TESTDIR / "oa_user_bottom_overlap.true")
    utils_for_tests.open_files_run_create(case_file, SCHEDULE, _TEST_FILE)
    utils_for_tests.assert_results(true_file, _TEST_FILE)


def test_oa_user_1vpj(tmpdir):
    """Test case with user defined segmentation and open annulus,
    with a 1 VPJ interval in the 0 VPJ lower parts of the well.
    """
    tmpdir.chdir()
    case_file = CASE_OA_USER_1VPJ
    true_file = Path(_TESTDIR / "oa_user_1vpj.true")
    utils_for_tests.open_files_run_create(case_file, SCHEDULE, _TEST_FILE)
    utils_for_tests.assert_results(true_file, _TEST_FILE)


def test_oa_user_user(tmpdir):
    """Test case with user defined segmentation and open annulus with a 1 VPJ
    interval in the 0 VPJ lower part of the well.
    """
    tmpdir.chdir()
    case_file = CASE_OA_USER_USER
    true_file = Path(_TESTDIR / "oa_user_1vpj.true")
    utils_for_tests.open_files_run_create(case_file, SCHEDULE, _TEST_FILE)
    utils_for_tests.assert_results(true_file, _TEST_FILE)


def test_oa_user_1vpj_pa(tmpdir):
    """Test completor case with user defined segmentation and open annulus with a
    1 VPJ interval in the 0 VPJ lower part of the well.

    Install a packer above in 1 VPJ interval in the lower part of the well.
    """
    tmpdir.chdir()
    case_file = CASE_OA_USER_1VPJ_PA
    true_file = Path(_TESTDIR / "oa_user_1vpj_pa.true")
    utils_for_tests.open_files_run_create(case_file, SCHEDULE, _TEST_FILE)
    utils_for_tests.assert_results(true_file, _TEST_FILE)


def test_oa_user_0vpj(tmpdir):
    """Test completor case with user defined segmentation and open annulus with a
    0 VPJ interval in the 1 VPJ upper part of the well.
    """
    tmpdir.chdir()
    case_file = CASE_OA_USER_0VPJ
    true_file = Path(_TESTDIR / "oa_user_0vpj.true")
    utils_for_tests.open_files_run_create(case_file, SCHEDULE, _TEST_FILE)
    utils_for_tests.assert_results(true_file, _TEST_FILE)


def test_oa_oneliner(tmpdir):
    """Test case with user-defined segmentation, open annulus given in one line, i.e. one segment.

    Include 0 - x and y - 99999.
    """
    tmpdir.chdir()
    case_file = CASE_OA_ONELINER
    true_file = Path(_TESTDIR / "oa_user_oneliner.true")
    utils_for_tests.open_files_run_create(case_file, SCHEDULE, _TEST_FILE)
    utils_for_tests.assert_results(true_file, _TEST_FILE)
