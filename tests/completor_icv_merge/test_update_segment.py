from pathlib import Path

import pandas as pd

from completor.constants import Keywords
from completor.main import create, get_content_and_path

_TESTDIR_COMPLETOR = Path(__file__).absolute().parent.parent / "completor" / "data"
_TESTDIR = Path(__file__).absolute().parent / "data"

with open(Path(_TESTDIR_COMPLETOR / "welldefinition.testfile"), encoding="utf-8") as file:
    WELL_DEFINITION = file.read()

case = Path(_TESTDIR / "icv_device_icvc.case")
schedule = Path(_TESTDIR_COMPLETOR / "icv_sch.sch")

with open(case, encoding="utf-8") as file:
    case_file_content = file.read()

schedule_file_content, schedule = get_content_and_path(case_file_content, schedule, Keywords.SCHEDULE_FILE)


def test_make_segment_list(tmpdir):
    _TEST_FILE = Path(tmpdir / "test.sch")
    case, well, well_segment = create(case_file_content, schedule_file_content, _TEST_FILE)
    df_new_segment = pd.DataFrame(well_segment, columns=["WELL", "NEW_SEGMENT"])
    df_true = pd.DataFrame(
        [
            [
                "A1",
                8,
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
