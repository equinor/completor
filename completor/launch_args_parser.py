"""Parser for launch arguments."""

from __future__ import annotations

import argparse

import completor

COMPLETOR_DESCRIPTION = """Completor models advanced well completions for reservoir simulators.
It generates all necessary keywords for reservoir simulation
according to a completion description. See the Completor Documentations
for modeling details.
"""


def get_parser() -> argparse.ArgumentParser:
    """Parse user input from the command line.

    Returns:
        argparse.ArgumentParser.
    """
    parser = argparse.ArgumentParser(description=COMPLETOR_DESCRIPTION)
    parser.add_argument("-i", "--inputfile", required=True, type=str, help="(Compulsory) Completor case file")
    parser.add_argument("-s", "--schedulefile", type=str, help="(Optional) if it is specified in the case file")
    parser.add_argument(
        "-o", "--outputfile", type=str, help="(Optional) name of output file. Defaults to <schedule>_advanced.wells"
    )
    parser.add_argument(
        "-f", "--figure", action="store_true", help="(Optional) to generate well completion diagrams in pdf format"
    )
    parser.add_argument(
        "-l", "--loglevel", action="store", type=int, help="(Optional) log-level. Lower values gives more info"
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="%(prog)s (completor version " + completor.__version__ + ")",
    )

    return parser
