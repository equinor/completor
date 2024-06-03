from __future__ import annotations

from completor import parse
from completor.constants import Headers


class _BaseCaseException(Exception):
    """Base for custom case exceptions."""

    def __init__(
        self, message: str, lines: list[str] | None = None, error_line: int | None = None, window_size: int = 5
    ):
        """Initialize the error message."""
        if lines is None or error_line is None:
            super().__init__(message)
        else:
            message = self._format_error_message(message, lines, error_line, window_size)
            super().__init__(message)

    def _format_error_message(self, message: str, original_lines: list[str], error_line: int, windows_size: int) -> str:
        """Format error message to show lines where the error occurred.

        The error is displayed with line numbers and ">" to indicate
        the line the error happened at. Then add the error message.

        Format example:
        .. code-block:: console
            Error at line 7:
            Could not parse "KEYWORD".
                5: KEYWORD
                6: -- Some comment
              > 7: data data something wrong /
                8: data data /
                9: /

        Args:
            message: Error message appended to the formatted error.
            original_lines: Lines in the original file the error happened at.
            error_line: What line the error occurred at.
            windows_size: How many lines from the file around the error should be
                displayed. (3=error_line-3:error_line+3).

        Returns:
            Error message formatted with lines from file where error occurred,
            arrow pointing at error line and error message.

        """
        # From 0 indexed to 1 indexed (like the actual file)
        start = self._clamp((error_line - windows_size), 0, len(original_lines))
        end = self._clamp((error_line + windows_size), 0, len(original_lines))

        lines = original_lines[start:end].copy()
        new_lines = []
        error_line += 1
        for i, line in enumerate(lines):
            shifted_index = i + start + 1
            if shifted_index == error_line:
                new_lines.append(f"> {str(shifted_index).rjust(len(str(end)))}: {line}")
            else:
                new_lines.append(f"  {str(shifted_index).rjust(len(str(end)))}: {line}")

        string = "\n".join(new_lines)
        return f"\n{string}\n\nError at line {error_line} in case file:\n{message}"

    @staticmethod
    def _clamp(n, minn, maxn):
        """Method for preventing index out of bounds."""
        return max(min(maxn, n), minn)


class CaseReaderFormatError(_BaseCaseException):
    """Used for keywords with faulty data/format."""

    error_index: int | None = None

    def __init__(
        self,
        message: str | None = None,
        lines: list[str] | None = None,
        header: list[str] | None = None,
        keyword: str | None = None,
        error_index: int | None = None,
        window_size: int = 5,
    ):
        if message is None:
            message = "Something went wrong while reading the casefile! "

        if lines is None or header is None:
            super().__init__(message)
            return

        extra_info = "few/many"
        if error_index is None:
            if keyword is None:
                super().__init__(message)
                return
            try:
                error_index, is_larger = CaseReaderFormatError.find_error_line(keyword, lines, header)
                extra_info = "many" if is_larger else "few"
            except Exception:  # pylint: disable=broad-exception-caught
                super().__init__(message)

        message += (
            f"Too {extra_info} entries in data for keyword '{keyword}', "
            f"expected {len(header)} entries: {header}!\n"
            "Please check the documentation for this keyword or "
            "contact the team directly if you believe this to be a mistake."
        )
        super().__init__(message, lines, error_index, window_size)

    @staticmethod
    def find_error_line(keyword: str, lines: list[str], header: list[str]):
        """Find line where error occurs.

        Args:
            keyword: Current keyword in case-file.
            lines: The (preferably) original case-file lines.
            header: The expected headers for this keyword.

        Raises:
            ValueError: If the line could not be found.

        Returns:
            Line number and whether there are too many/few data entries vs header.

        """
        stripped_content = [x.strip() for x in lines]
        start, end = parse.locate_keyword(stripped_content, keyword)

        line_content = {
            i + start + 1: line for i, line in enumerate(lines[start + 1 : end]) if line and not line.startswith("--")
        }

        for line, content in line_content.items():
            if len(content.strip().split()) != len(header):
                return line, len(header) < len(content.strip().split())

        raise ValueError("Could not find the erroneous line.")
