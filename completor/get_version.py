"""Only used to get the version."""

from importlib import metadata


def get_version():
    """Returns Completors version."""
    return metadata.version("completor")
