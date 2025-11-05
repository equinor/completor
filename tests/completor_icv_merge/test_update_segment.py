from pathlib import Path

import pandas as pd
import pytest

from completor import read_casefile
from completor.constants import Keywords
from completor.exceptions.clean_exceptions import CompletorError
from completor.main import create, get_content_and_path
from tests.utils_for_tests import completor_runner

_TESTDIR_COMPLETOR = Path(__file__).absolute().parent.parent / "completor" / "data"
_TESTDIR = Path(__file__).absolute().parent / "data"
_TEST_FILE = "test.sch"

with open(Path(_TESTDIR_COMPLETOR / "welldefinition.testfile"), encoding="utf-8") as file:
    WELL_DEFINITION = file.read()

case = Path(_TESTDIR / "icv_device_icvc.case")
schedule = Path(_TESTDIR_COMPLETOR / "icv_sch.sch")

with open(case, encoding="utf-8") as file:
    case_file_content = file.read()

schedule_file_content, schedule = get_content_and_path(case_file_content, str(schedule), Keywords.SCHEDULE_FILE)


def test_make_segment_list(tmpdir):
    "Test make ICV segment list from Completor output"
    _TEST_FILE = Path(tmpdir / "test.sch")
    _, _, well_segment = create(case_file_content, schedule_file_content, _TEST_FILE)
    df_new_segment = pd.DataFrame(well_segment, columns=["WELL", "NEW_SEGMENT"])
    df_true = pd.DataFrame(
        [
            [
                "A1",
                8,
            ],
            [
                "A1",
                2,
            ],
            [
                "A2",
                4,
            ],
        ],
        columns=[
            "WELL",
            "NEW_SEGMENT",
        ],
    )
    pd.testing.assert_frame_equal(df_true, df_new_segment)


def test_make_segment_multilateral(tmpdir):
    "Test make ICV segment list from Completor output for multilateral wells"
    case_drogon = Path(_TESTDIR / "case_test.case")
    schedule_drogon = Path(_TESTDIR / "schedule.sch")
    with open(case_drogon, encoding="utf-8") as file:
        case_file_content = file.read()
    schedule_file_content, schedule_drogon = get_content_and_path(
        case_file_content, str(schedule_drogon), Keywords.SCHEDULE_FILE
    )
    _TEST_FILE = Path(tmpdir / "test.sch")
    _, _, well_segment = create(case_file_content, schedule_file_content, _TEST_FILE)
    df_new_segment = pd.DataFrame(well_segment, columns=["WELL", "NEW_SEGMENT"])
    df_true = pd.DataFrame(
        [
            [
                "A2",
                6,
            ],
            [
                "A3",
                16,
            ],
            [
                "A4",
                2,
            ],
            [
                "A5",
                8,
            ],
            [
                "A5",
                9,
            ],
            [
                "A6",
                9,
            ],
            [
                "A6",
                10,
            ],
            [
                "OP5",
                16,
            ],
            [
                "OP5",
                5,
            ],
            [
                "OP5",
                37,
            ],
            [
                "OP5",
                28,
            ],
        ],
        columns=[
            "WELL",
            "NEW_SEGMENT",
        ],
    )
    pd.testing.assert_frame_equal(df_true, df_new_segment)


def test_update_segment(tmpdir):
    "Test update ICV segment to ICVCONTROL case file."
    case_drogon = Path(_TESTDIR / "case_test.case")
    schedule_drogon = Path(_TESTDIR / "schedule.sch")
    _TEST_FILE = Path(tmpdir / "test.sch")
    with open(case_drogon, encoding="utf-8") as file:
        case_file_content = file.read()
    schedule_file_content, schedule_drogon = get_content_and_path(
        case_file_content, str(schedule_drogon), Keywords.SCHEDULE_FILE
    )

    _, _, well_segment = create(case_file_content, schedule_file_content, _TEST_FILE)
    df_icv_case = read_casefile.ICVReadCasefile(
        case_file_content, schedule_file_content, well_segment
    ).icv_control_table

    df_true = pd.DataFrame(
        [
            ["A2", "A2", 6, "A", 100, "2.JAN.2020", 30, 1.0, 10.0, "T10", 1.0, 10.0, 0.1, 2.0, 1.0, 0.01],
            ["A3", "A3", 16, "A", 100, "2.JAN.2020", 30, 3.0, 10.0, "T10", 1.0, 10.0, 0.1, 2.0, 1.0, 0.01],
            ["A4", "A4", 2, "A", 100, "2.JAN.2020", 30, 1.0, 7.0, "T5", 1.0, 10.0, 0.1, 2.0, 1.0, 0.01],
            ["A5", "A5", 8, "A", 100, "2.JAN.2020", 30, 1.0, 7.0, "T5", 1.0, 10.0, 0.1, 2.0, 1.0, 0.01],
            ["A5", "A5", 9, "A", 100, "2.JAN.2020", 30, 1.0, 7.0, "T5", 1.0, 10.0, 0.1, 2.0, 1.0, 0.01],
            ["A6", "A6", 9, "A", 100, "2.JAN.2020", 30, 1.0, 7.0, "T5", 1.0, 10.0, 0.1, 2.0, 1.0, 0.01],
            ["A6", "A6", 10, "A", 100, "2.JAN.2020", 30, 1.0, 7.0, "T5", 1.0, 10.0, 0.1, 2.0, 1.0, 0.01],
            ["OP5", "O3", 16, "A", 100, "2.JAN.2020", 30, 1.0, 10.0, "T10", 1.0, 10.0, 0.1, 2.0, 1.0, 0.01],
            ["OP5", "O1", 5, "A", 100, "2.JAN.2020", 30, 1.0, 10.0, "T10", 1.0, 10.0, 0.1, 2.0, 1.0, 0.01],
            ["OP5", "O4", 37, "A", 100, "2.JAN.2020", 30, 1.0, 10.0, "T10", 1.0, 10.0, 0.1, 2.0, 1.0, 0.01],
            ["OP5", "O2", 28, "A", 100, "2.JAN.2020", 30, 1.0, 10.0, "T10", 1.0, 10.0, 0.1, 2.0, 1.0, 0.01],
        ],
        columns=[
            "WELL",
            "ICV",
            "SEGMENT",
            "AC-TABLE",
            "STEPS",
            "ICVDATE",
            "FREQ",
            "MIN",
            "MAX",
            "OPENING",
            "FUD",
            "FUH",
            "FUL",
            "OPERSTEP",
            "WAITSTEP",
            "INIT",
        ],
    )
    pd.testing.assert_frame_equal(df_true, df_icv_case)


def test_update_segment_mismatch(tmpdir):
    "Test error message when number of ICV does not match the whole ICVCONTROL table"
    tmpdir.chdir()
    case_drogon = Path(_TESTDIR / "case_test_wrong.case")
    schedule_drogon = Path(_TESTDIR / "schedule.sch")
    expected_error_message = "ICVs defined in ICVCONTROL table are 10 while the ICVs found in schedule file are 11"
    with pytest.raises(CompletorError) as e:
        completor_runner(inputfile=case_drogon, schedulefile=schedule_drogon, outputfile=_TEST_FILE)
    assert expected_error_message in str(e.value)


def test_update_segment_mismatch_well(tmpdir):
    "Test error message when number of ICV does not match specific wells"
    tmpdir.chdir()
    case_drogon = Path(_TESTDIR / "case_test_wrong2.case")
    schedule_drogon = Path(_TESTDIR / "schedule.sch")
    expected_error_message = "Number of ICVs defined in ICV Case for well A5 are not the same as Completor output."
    with pytest.raises(CompletorError) as e:
        completor_runner(inputfile=case_drogon, schedulefile=schedule_drogon, outputfile=_TEST_FILE)
        # utils_for_tests.open_files_run_create(case_drogon, schedule_drogon, _TEST_FILE)
    assert expected_error_message in str(e.value)
