"""Utilities for testing."""

from argparse import Namespace

from completor import main


def _mock_parse_args(**kwargs):

    # Set default values.
    kwargs["loglevel"] = 0 if kwargs.get("loglevel") is None else kwargs["loglevel"]
    kwargs["figure"] = False if kwargs.get("figure") is None else kwargs["figure"]
    kwargs["schedulefile"] = None if kwargs.get("schedulefile") is None else kwargs["schedulefile"]
    kwargs["outputfile"] = None if kwargs.get("outputfile") is None else kwargs["outputfile"]

    def _mock_get_parser():
        class MockObject:
            @staticmethod
            def parse_args() -> Namespace:
                return Namespace(**kwargs)

        return MockObject

    setattr(main, "get_parser", _mock_get_parser)


def completor_runner(**kwargs) -> None:
    """
    Helper function to run completor as if it was launched as a CLI program.

    Function mocks args_parser and makes it return the values specified in **kwargs.

    Args:
        kwargs: Keyword arguments to run completor with.

    """
    _mock_parse_args(**kwargs)
    main.main()
