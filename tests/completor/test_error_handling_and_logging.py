from __future__ import annotations

import json
import re
from pathlib import Path
from zipfile import ZipFile

import pytest
from utils import completor_runner

_testdir = Path(__file__).absolute().parent / "data"
_test_file = "ml_well.sch"

_debug_information_file_name_pattern = re.compile(r"^Completor-\d{8}-\d{6}-\w\d{5}.zip$")


def test_debug_information_is_written_to_disk_on_failure(tmpdir, caplog):
    """
    Check if completor writes debug information to disk in the event of a failure.
    """
    tmpdir.chdir()
    case_file = str(_testdir / "usestrict_default_missingbranch.casefile")
    sch_file = str(_testdir / "ml_well.sch")

    with pytest.raises(SystemExit) as exc:
        completor_runner(inputfile=case_file, schedulefile=sch_file, outputfile=_test_file)
    files = tmpdir.listdir()
    assert exc.value.code == 1
    assert len(files) == 2  # One schedule file, and one zip file
    assert any(_debug_information_file_name_pattern.match(file.basename) for file in files)
    assert "USE_STRICT True: Define all branches in case file." in caplog.messages

    # Check the content of the debug information
    for file in files:
        match = _debug_information_file_name_pattern.match(file.basename)
        if match:
            file_name = match.group()
            break

    expected_files = [
        "traceback.txt",
        "machine.txt",
        "version.txt",
        "arguments.json",
        "input_file.txt",
        "schedule_file.txt",
        "new_file.txt",
    ]
    expected_arguments = {"input_file": case_file, "schedule_file": sch_file, "new_file": _test_file, "show_fig": False}
    base_directory, suffix = file_name.split(".")
    with ZipFile(file_name, "r") as debug_information:
        actual_files = [file.filename.split("/")[-1] for file in debug_information.filelist]
        assert expected_files == actual_files
        with debug_information.open(f"{base_directory}/arguments.json") as f:
            actual_arguments = json.load(f)
        assert expected_arguments == actual_arguments

        def compare_file_content(expected: str, actual: str):
            with open(expected, encoding="utf-8") as expected_file:
                with debug_information.open(f"{base_directory}/{actual}", "r") as actual_file:
                    assert expected_file.read() == actual_file.read().decode("utf-8")

        compare_file_content(case_file, "input_file.txt")
        compare_file_content(sch_file, "schedule_file.txt")
        # The output file should not be changed
