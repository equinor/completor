"""Test function for Completor with Drogon."""

from pathlib import Path

import pytest
import utils_for_tests

from completor.constants import Keywords

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
        "dualrcp1_gp.case",
        "dualrcp6_gp_oa.case",
        "dualrcp6_gp_oa_pa1.case",
        "dualrcp6_oa.case",
        "dualrcp6_pa3.case",
        "density1_gp.case",
        "density6_gp_oa.case",
        "density6_gp_oa_pa1.case",
        "density6_oa.case",
        "density6_pa3.case",
        "density6_perf_aicd6_gp_oa.case",
        "icd1_gp.case",
        "icd6_gp_oa.case",
        "icd6_gp_oa_pa1.case",
        "icd6_oa.case",
        "icd6_pa3.case",
        "icv_aicd_gp_oa_pa.case",
        "icv_aicd_tubing.case",
        "icv_aicd.case",
        "icv1_oa.case",
        "icv6_gp_oa_pa.case",
        "injection_valve1_gp.case",
        "injection_valve6_oa.case",
        "injection_valve6_pa3.case",
        "injection_valve6_gp_oa_pa1.case",
        "injection_valve6_gp_oa.case",
        "injection_valve6_perf_aicd6_gp_oa.case",
        "perf6_oa.case",
        "perf_aicd6_oa_gp.case",
        "perf_aicd6_oa_gp_pa1.case",
        "perf_dualrcp6_oa_gp.case",
        "perf_dualrcp6_oa_gp_pa1.case",
        "perf_density6_oa_gp.case",
        "perf_density6_oa_gp_pa1.case",
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
    schedule_name = lines[lines.index(Keywords.SCHEDULE_FILE) + 1]
    schedule_path = Path(_TESTDIR_DROGON / schedule_name)
    true_file = Path(_TESTDIR_DROGON / drogon_case.replace(".case", ".true"))
    utils_for_tests.open_files_run_create(case_path, schedule_path, _TEST_FILE)
    #with open(_TEST_FILE, encoding="utf-8") as file:
    #    result = file.read() 
    #print(result)    
    utils_for_tests.assert_results(true_file, _TEST_FILE)


@pytest.mark.parametrize("drogon_case", ["icv1_gp.case"])
def test_drogon_cases_with_text_match(drogon_case: str, tmpdir):
    """Test Completor with Drogon cases."""
    # Copy pvt file to tmpdir before creating schedule files
    tmpdir.chdir()
    case_path = Path(_TESTDIR_DROGON / drogon_case)
    with open(case_path, encoding="utf-8") as case_file:
        case_data = case_file.read()
        lines = case_data.splitlines()
    schedule_name = lines[lines.index(Keywords.SCHEDULE_FILE) + 1]
    schedule_path = Path(_TESTDIR_DROGON / schedule_name)
    true_file = Path(_TESTDIR_DROGON / drogon_case.replace(".case", ".true"))
    utils_for_tests.open_files_run_create(case_path, schedule_path, _TEST_FILE)
    utils_for_tests.assert_results(true_file, _TEST_FILE, assert_text=True)
