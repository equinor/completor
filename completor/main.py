"""Main module of Completor."""

from __future__ import annotations

import argparse
import logging
import os
import re
import time
from collections.abc import Callable, Mapping
from typing import overload

import numpy as np

import completor
from completor import parse
from completor.completion import WellSchedule
from completor.constants import Keywords
from completor.create_output import CreateOutput
from completor.create_wells import CreateWells
from completor.logger import handle_error_messages, logger
from completor.read_casefile import ReadCasefile
from completor.utils import abort, clean_file_line, clean_file_lines, get_completor_version
from completor.visualization import close_figure, create_pdfpages

try:
    from typing import Literal
except ImportError:
    pass


def create_get_well_name(schedule_lines: dict[int, str]) -> Callable[[int], str]:
    """
    Create a function to get the well name from line number.

    Args:
        schedule_lines: All lines in schedule file

    Returns:
        get_well_name (Function)
    """
    keys = np.array(sorted(list(schedule_lines.keys())))

    def get_well_name(line_number: int) -> str:
        """
        Get well name for WELSEGS or COMPSEGS.

        Assumes that line_number points to one of these keywords.

        Args:
            line_number: Line number

        Returns:
            Well name

        """
        i = (keys == line_number).nonzero()[0][0]
        next_line = schedule_lines[keys[i + 1]]
        return next_line.split()[0]

    return get_well_name


def format_chunk(chunk_str: str) -> list[list[str]]:
    """
    Format the data-records and resolve the repeat-mechanism of Eclipse.

    E.g. 3* == 1* 1* 1*, 3*250 == 250 250 250

    Args:
        chunk_str: A chunk data-record

    Returns:
        Expanded Eclipse values
    """
    chunk = re.split(r"\s+/", chunk_str)[:-1]
    expanded_data = []
    for line in chunk:
        new_record = ""
        for record in line.split():
            if not record[0].isdigit():
                new_record += record + " "
                continue
            if "*" not in record:
                new_record += record + " "
                continue

            # need to handle things like 3* or 3*250
            multiplier, number = record.split("*")
            new_record += f"{number if number else '1*'} " * int(multiplier)
        if new_record:
            expanded_data.append(new_record.split())
    return expanded_data


class FileWriter:
    """Functionality for writing a new schedule file."""

    def __init__(self, file: str, mapper: Mapping[str, str] | None):
        """
        Initialize the FileWriter.

        Args:
            file_name: Name of file to be written. Does not check if it already exists.
            mapper: A dictionary for mapping strings. Typically used for mapping RMS
                    well names to Eclipse well names
        """
        self.fh = open(file, "w", encoding="utf-8")  # create new output file
        self.mapper = mapper

    @overload
    def write(self, keyword: Literal[None], content: str, chunk: bool = True, end_of_record: bool = False) -> None: ...

    @overload
    def write(
        self, keyword: str, content: list[list[str]], chunk: Literal[True] = True, end_of_record: bool = False
    ) -> None: ...

    @overload
    def write(
        self, keyword: str, content: list[str] | str, chunk: Literal[False] = False, end_of_record: bool = False
    ) -> None: ...

    @overload
    def write(
        self, keyword: str, content: list[list[str]] | list[str] | str, chunk: bool = True, end_of_record: bool = False
    ) -> None: ...

    def write(
        self,
        keyword: str | None,
        content: list[list[str]] | list[str] | str,
        chunk: bool = True,
        end_of_record: bool = False,
    ) -> None:
        """
        Write the content of a keyword to the output file.

        Args:
            keyword: Eclipse keyword
            content: Text to be written. string, string-list or record-list
            chunk: Flag for indicating this is a list of records.
            end_of_record: Flag for adding end-of-record ('/')
        """
        txt = ""  # to be written

        if keyword is None:
            txt = content  # type: ignore  # it's really a formatted string
        else:
            self.fh.write(f"{keyword:s}\n")
            if chunk:
                for recs in content:
                    txt += " " + " ".join(recs) + " /\n"
            else:
                for line in content:
                    if isinstance(line, list):
                        logger.warning(
                            "chunk is False, but content contains lists of lists, "
                            "instead of a list of strings the lines will be "
                            "concatenated"
                        )
                        line = " ".join(line)
                    txt += line + "\n"
        if self.mapper:
            txt = self._replace_rms_names(txt)
        if end_of_record:
            txt += "/\n"
        self.fh.write(txt)

    def _replace_rms_names(self, text: str) -> str:
        """
        Expand start and end marker pairs for well pattern recognition as needed.

        Args:
            text: Text with RMS well names

        Returns:
            Text with Eclipse well names
        """
        if self.mapper is None:
            raise ValueError(
                f"{self._replace_rms_names.__name__} requires a file containing two "
                "columns with input and output names given by the MAPFILE keyword in "
                f"case file to be set when creating {self.__class__.__name__}."
            )
        start_marks = ["'", " ", "\n", "\t"]
        end_marks = ["'", " ", " ", " "]
        for key, value in self.mapper.items():
            for start, end in zip(start_marks, end_marks):
                my_key = start + str(key) + start
                if my_key in text:
                    my_value = start + str(value) + end
                    text = text.replace(my_key, my_value)
        return text

    def close(self) -> None:
        """Close FileWriter."""
        self.fh.close()


class ProgressStatus:
    """
    Bookmark the reading progress of a schedule file.

    See https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console
    for improved functionality.
    """

    def __init__(self, num_lines: int, percent: float):
        """
        Initialize ProgressStatus.

        Args:
            num_lines: Number of lines in schedule file
            percent: Indicates schedule file processing progress (in per cent)
        """
        self.percent = percent
        self.nlines = num_lines
