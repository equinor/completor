from __future__ import annotations

import ert  # type: ignore

from completor.hook_implementations import RunCompletor
from completor.logger import logger

PLUGIN_NAME = "completor"

try:
    from ert.plugins.plugin_manager import ErtPluginManager  # type: ignore # noqa: F401
except ModuleNotFoundError:

    def ert_plugin(name: str = ""):
        """Dummy decorator"""

        def decorator(func):
            return func

        return decorator

    logger.warning("Cannot import ERT, did you install Completor with ert option enabled?")


@ert.plugin(name=PLUGIN_NAME)
def installable_workflow_jobs() -> dict[str, str]:
    return {}


@ert.plugin(name=PLUGIN_NAME)
def installable_forward_model_steps() -> list[ert.ForwardModelStepPlugin]:
    return [RunCompletor]
