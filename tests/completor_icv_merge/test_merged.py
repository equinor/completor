import os
import shutil
from pathlib import Path

from tests.utils_for_tests import _assert_file_output, assert_files_exist_and_nonempty, completor_runner

_TESTDIR_COMPLETOR = Path(__file__).absolute().parent.parent / "completor" / "data"
_TESTDIR = Path(__file__).absolute().parent / "data"

with open(Path(_TESTDIR_COMPLETOR / "welldefinition.testfile"), encoding="utf-8") as file:
    WELL_DEFINITION = file.read()

case = Path(_TESTDIR / "init.case")
schedule = Path(_TESTDIR_COMPLETOR / "welldefinition.testfile")


def test_assert_files_merge_run_output(tmpdir):
    tmpdir.chdir()
    completor_runner(inputfile=case, schedulefile=schedule, outputfile="test.out")
    assert_files_exist_and_nonempty(
        [
            "summary_icvc.sch",
            "include_icvc.sch",
            "test.out",
        ]
    )


def test_contents_schedule_output_merged(tmpdir):
    tmpdir.chdir()
    completor_runner(inputfile=case, schedulefile=schedule, outputfile="test.out")
    true_file = Path(_TESTDIR / "test_out.true")
    out_file = Path("test.out")
    _assert_file_output(out_file, true_file)


def test_output_fmu_directory(tmpdir):
    input_dir = tmpdir / "lvl1" / "lvl2" / "lvl3"
    case = Path(input_dir / "field")
    case.mkdir(parents=True)
    sch = Path(input_dir / "include" / "schedule")
    sch.mkdir(parents=True),
    shutil.copy(_TESTDIR / "init.case", case)
    shutil.copy(_TESTDIR_COMPLETOR / "welldefinition.testfile", sch)
    os.chdir(input_dir)

    completor_runner(
        inputfile="field/init.case",
        schedulefile="include/schedule/welldefinition.testfile",
        outputfile="include/schedule/output.sch",
    )

    assert_files_exist_and_nonempty(
        [
            "include/schedule/summary_icvc.sch",
            "include/schedule/include_icvc.sch",
            "include/schedule/output.sch",
        ]
    )


def test_output_fmu_default_name(tmpdir):
    input_dir = tmpdir / "lvl1" / "lvl2" / "lvl3"
    case = Path(input_dir / "field")
    case.mkdir(parents=True)
    sch = Path(input_dir / "include" / "schedule")
    sch.mkdir(parents=True),
    shutil.copy(_TESTDIR / "init.case", case)
    shutil.copy(_TESTDIR_COMPLETOR / "welldefinition.testfile", sch)
    os.chdir(input_dir)

    completor_runner(inputfile="field/init.case", schedulefile="include/schedule/welldefinition.testfile")

    assert_files_exist_and_nonempty(
        [
            "include/schedule/summary_icvc.sch",
            "include/schedule/include_icvc.sch",
            "include/schedule/welldefinition_advanced.wells",
        ]
    )
