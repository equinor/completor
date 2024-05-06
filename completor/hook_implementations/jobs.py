"""Configuration for running Completor as a plugin in ERT."""

from __future__ import annotations

from pathlib import Path

from pkg_resources import resource_filename

from completor.logger import logger

SKIP_TESTS = False
try:
    from ert.shared.plugins.plugin_manager import hook_implementation  # type: ignore
    from ert.shared.plugins.plugin_response import plugin_response  # type: ignore

except ModuleNotFoundError:
    logger.warning("Cannot import ERT, did you install Completor with ert option enabled?")
    pass


@hook_implementation
@plugin_response(plugin_name="completor")
def installable_jobs() -> dict[str, Path]:
    config_file = Path(resource_filename("completor", "config_jobs/run_completor"))
    return {config_file.name: config_file}


@hook_implementation
@plugin_response(plugin_name="completor")  # type: ignore  # pylint: disable=no-value-for-parameter
def job_documentation(job_name: str) -> dict[str, str] | None:
    if job_name != "run_completor":
        return None

    description = """Completor is a script for modelling
wells with advanced completion.
It generates a well schedule to be included in Eclipse/OPM Flow,
by combining the multi-segment tubing definition (from RMS, ResInsight, PetrelRE etc.)
with a user defined file specifying the completion design.
The resulting well schedule comprises all keywords and parameters required by
Eclipse/OPM Flow. See the Completor Wiki for details.

Required:
---------
-i   : followed by name of file specifying completion design (e.g. completion.case).
-s   : followed by name of schedule file with multi-segment tubing definition,
       including COMPDAT, COMPSEGS and WELSEGS (required if not specified in case file).
-p   : followed by name of a pvt file (required for completions with DAR and AICV).

Optional:
---------
--help   : how to run completor.
--about  : about completor.
-o       : followed by name of completor output file.
--figure  : generates a pdf file with a schematics of the well segment structure.

"""

    examples = """.. code-block:: console
  FORWARD_MODEL run_completor(
    <CASE>=path/to/completion.case,
    <INPUT_SCH>=path/to/input.sch,
    <OUTPUT_SCH>path/to/output.sch
)
"""

    category = "modelling.reservoir"

    return {"description": description, "examples": examples, "category": category}
