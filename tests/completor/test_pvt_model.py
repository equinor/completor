"""Test functions for the Completor pvt_model module."""

from pathlib import Path

from completor import pvt_model  # type: ignore

_TESTDIR = Path(__file__).absolute().parent / "data"


def test_correlation_udq():
    """Test the function which gives the AICV UDQ expression of SUWCT."""
    expected = """UDQ
--Water cut definition
DEFINE SUWCT NINT(SWHF*100/(SWHF+SOHF+1e-20))/100 /
/


"""
    assert expected == pvt_model.CORRELATION_UDQ
