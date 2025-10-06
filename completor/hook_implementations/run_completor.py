from __future__ import annotations

from ert import ForwardModelStepDocumentation, ForwardModelStepJSON, ForwardModelStepPlugin  # type: ignore

desc = """Completor is a script for modelling
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


class RunCompletor(ForwardModelStepPlugin):
    def __init__(self) -> None:
        super().__init__(
            name="run_completor",
            command=[
                "run_completor",
                "-i",
                "<CASE>",
                "-s",
                "<INPUT_SCH>",
                "-o",
                "<OUTPUT_SCH>",
            ],
        )

    def validate_pre_realization_run(self, fm_step_json: ForwardModelStepJSON) -> ForwardModelStepJSON:
        return fm_step_json

    def validate_pre_experiment(self, fm_step_json: ForwardModelStepJSON) -> None:
        pass

    @staticmethod
    def documentation() -> ForwardModelStepDocumentation | None:
        return ForwardModelStepDocumentation(
            category="modelling.reservoir",
            source_package="completor",
            source_function_name="RunCompletor",
            description=desc,
            examples="""
.. code-block:: console
  FORWARD_MODEL run_completor(<CASE>=case_completor.case, <INPUT_SCH>=drogon_pred.sch, <OUTPUT_SCH>=drogon_pred_ict.sch)
""",
        )
