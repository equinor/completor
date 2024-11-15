import sys
from pathlib import Path

from completor.logger import logger

try:
    from ert import plugin as ert_plugin  # type: ignore
except ModuleNotFoundError:

    def ert_plugin(name: str = ""):
        """Dummy decorator"""

        def decorator(func):
            return func

        return decorator

    logger.warning("Cannot import ERT, did you install Completor with ert option enabled?")


def _get_jobs_from_directory(directory):
    resources = Path(sys.modules["completor"].__file__).parent / directory

    all_files = [resources / filename for filename in resources.glob("*") if (resources / filename).exists()]
    return {path.name: str(path) for path in all_files}


@ert_plugin(name="completor")
def installable_jobs():
    return _get_jobs_from_directory("config_jobs")


@ert_plugin(name="completor")
def job_documentation(job_name):
    if job_name != "run_completor":
        return None

    description = """Completor is a script for modelling
wells with advanced completion.
It generates a well schedule to be included in reservoir simulator,
by combining the multi-segment tubing definition (from pre-processor reservoir modelling tools)
with a user defined file specifying the completion design.
The resulting well schedule comprises all keywords and parameters required by
reservoir simulator. See the Completor documentation for details.

Required:
---------
-i   : followed by name of file specifying completion design (e.g. completion.case).
-s   : followed by name of schedule file with multi-segment tubing definition,
       including COMPDAT, COMPSEGS and WELSEGS (required if not specified in case file).

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
