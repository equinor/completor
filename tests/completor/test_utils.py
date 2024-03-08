import re

from completor.utils import clean_file_line, clean_file_lines, get_completor_version


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
