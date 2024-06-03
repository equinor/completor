"""Test function for Completor with Drogon."""

from pathlib import Path

import common
import pytest

_TESTDIR_DROGON = Path(__file__).absolute().parent / "data" / "drogon"
_TEST_FILE = "test.sch"


@pytest.mark.parametrize(
    "drogon_case",
    [
        "aicd1_gp.case",
        "aicd6_gp.case",
        "aicd6_gp_oa.case",
        "aicd6_gp_oa_pa1.case",
        "aicd6_oa.case",
        "aicd6_pa3.case",
        "aicv1_gp.case",
        "aicv6_gp_oa.case",
        "aicv6_gp_oa_pa1.case",
        "aicv6_oa.case",
        "aicv6_pa3.case",
        "dar1_gp.case",
        "dar6_gp_oa.case",
        "dar6_gp_oa_pa1.case",
        "dar6_oa.case",
        "dar6_pa3.case",
        "dar6_perf_aicd6_gp_oa.case",
        "icd1_gp.case",
        "icd6_gp_oa.case",
        "icd6_gp_oa_pa1.case",
        "icd6_oa.case",
        "icd6_pa3.case",
        "icv_aicd_gp_oa_pa.case",
        "icv_aicd_tubing.case",
        "icv_aicd.case",
        "icv1_gp.case",
        "icv1_oa.case",
        "icv6_gp_oa_pa.case",
        "perf6_oa.case",
        "perf_aicd6_oa_gp.case",
        "perf_aicd6_oa_gp_pa1.case",
        "perf_aicv6_oa_gp.case",
        "perf_aicv6_oa_gp_pa1.case",
        "perf_dar6_oa_gp.case",
        "perf_dar6_oa_gp_pa1.case",
        "perf_gp_bp.case",
        "perf_gp.case",
        "perf_gp_oa.case",
        "perf_gp_oa_pa1.case",
        "perf_gp_peqvr_default.case",
        "perf_icd6_gp_oa.case",
        "perf_icd6_gp_oa_pa1.case",
        "perf_oa.case",
        "perf_oa_patop.case",
        "perf_pa3.case",
        "perf_valve6_gp_oa.case",
        "perf_valve6_gp_oa_pa1.case",
        "valve1_gp.case",
        "valve6_gp_oa.case",
        "valve6_gp_oa_pa1.case",
        "valve6_oa.case",
        "valve6_pa3.case",
    ],
)
def test_drogon_cases(drogon_case: str, tmpdir):
    """Test Completor with Drogon cases."""

    # Copy pvt file to tmpdir before creating schedule files
    tmpdir.chdir()
    case_path = Path(_TESTDIR_DROGON / drogon_case)
    with open(case_path, encoding="utf-8") as case_file:
        lines = [line.strip("\n") for line in case_file.readlines()]
    schedule_name = lines[lines.index("SCHFILE") + 1]
    schedule_path = Path(_TESTDIR_DROGON / schedule_name)
    true_file = Path(_TESTDIR_DROGON / drogon_case.replace(".case", ".true"))
    common.open_files_run_create(case_path, schedule_path, _TEST_FILE)
    common.assert_results(true_file, _TEST_FILE)
