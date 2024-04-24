import re

import completor
from completor.utils import clean_file_line, clean_file_lines


def test_clean_file_line_with_file_path():
    """
    Test that the file path is preserved.

    Leading and trailing white space should be removed.
    File path should remain untouched, but trailing comments removed.
    """
    test = "'some/file/path/test.case'"
    assert clean_file_line(test) == "'some/file/path/test.case'"
    test_white_space = "\t'some/file/path/test.case'\t      "
    assert clean_file_line(test_white_space) == "'some/file/path/test.case'"
    test_with_comment = "\t'some/file/path/test.case'\t     / A comment"
    assert clean_file_line(test_with_comment) == "'some/file/path/test.case' /"


def test_clean_file_line_comment():
    """Test that a comment line is changed to an empty string."""
    test = "--AICD_NUMBER Alpha x   y   a   b   c   d   e   f   Rho_Cal Vis_Cal"
    assert clean_file_line(test) == ""


def test_clean_file_line_with_well_name_quotes():
    """
    Test clean_file_line with well name in quotes.

    Should keep trailing comment by default.
    Should remove quotes and trailing comment if remove set to true.
    Should preserve quoted well name containing a '/'.
    """
    clean_test = "\t'A1'       35   113    72    72  OPEN    / trailing comment"
    true_with_quotes = "'A1' 35 113 72 72 OPEN /"
    assert clean_file_line(clean_test) == true_with_quotes
    true_removed_quotes = "A1 35 113 72 72 OPEN /"
    assert clean_file_line(clean_test, remove_quotation_marks=True) == true_removed_quotes
    clean_test_with_slash = "\t'A/1'       35   113    72    72  OPEN    / trailing comment"
    true_test_with_slash = "'A/1' 35 113 72 72 OPEN /"
    assert clean_file_line(clean_test_with_slash) == true_test_with_slash


def test_clean_file_lines():
    """
    Test the clean_file_lines function.

    Should remove all comments and empty lines.
    Should remove trailing comments, but preserve file paths and quoted well names.
    """
    test_lines = [
        "COMPDAT",
        "--WELL",
        "-----------------------------",
        "\tA1       35   113    72  / trailing comment",
        "\t'A1'       35   113    72  / trailing comment",
        '\t"A1"       35   113    72  / trailing comment',
        "\t'A/1'       35   113    72  / trailing comment",
        "/",
    ]
    true_lines = [
        "COMPDAT",
        "A1 35 113 72 /",
        "'A1' 35 113 72 /",
        '"A1" 35 113 72 /',
        "'A/1' 35 113 72 /",
        "/",
    ]
    assert clean_file_lines(test_lines) == true_lines


# @pytest.mark.skip
def test_version_is_canonical():
    """
    Test that the version format is correct.

    Version format should match 'vX.X.X' where X is a valid digit.
    A version digit should be either 0 or start with 1-9.
    """
    version = completor.__version__
    # Regex for checking correct format
    # assert re.match(
    #     r"^v(0|[1-9]\d*)\.(0|[1-9\d]*)\.(0|[1-9\d]*)$", version
    # ), "Version has incorrect format. Should be on the form v1.2.3"

    pattern = r"^([1-9][0-9]*!)?(0|[1-9][0-9]*)(\.(0|[1-9][0-9]*))*((a|b|rc)(0|[1-9][0-9]*))?(\.post(0|[1-9][0-9]*))?(\.dev(0|[1-9][0-9]*))?$"  # noqa: E501
    assert re.match(pattern, version) is not None
