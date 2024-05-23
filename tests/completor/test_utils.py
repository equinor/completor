import pytest

from completor.utils import clean_file_line, clean_file_lines


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("'some/file/path/test.case'", "'some/file/path/test.case'"),
        ("\t'some/file/path/test.case'\t      ", "'some/file/path/test.case'"),
        ("\t'some/file/path/test.case'\t     / A comment", "'some/file/path/test.case' /"),
        ("  '../some/file/path/test.case'/comment", "'../some/file/path/test.case'/"),
        ("'../some/file/path/test.case'", "'../some/file/path/test.case'"),
    ],
)
def test_clean_file_line_with_file_path(test_input: str, expected: str) -> None:
    """
    Test that the file path is preserved.

    Leading and trailing white space should be removed.
    File path should remain untouched, but trailing comments removed.
    """
    assert clean_file_line(test_input) == expected


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
