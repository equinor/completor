"""Separate file for exceptions that don't need parser, this is needed to avoid circular imports from parser.py"""


class CompletorError(Exception):
    """Custom error for completor, if anything goes critically wrong in completor this error will be raised.
    This error is caught in main initiating the abort function and will terminate the program.
    """

    pass
