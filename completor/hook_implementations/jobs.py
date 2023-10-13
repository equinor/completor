from pathlib import Path

from ert.shared.plugins.plugin_manager import hook_implementation  # type: ignore
from ert.shared.plugins.plugin_response import plugin_response  # type: ignore
from pkg_resources import resource_filename


@hook_implementation
@plugin_response(plugin_name="completor")  # type: ignore
def installable_jobs():
    config_file = Path(resource_filename("completor", "completor/config_jobs/run_completor"))
    return {config_file.name: config_file}


@hook_implementation
@plugin_response(plugin_name="completor")  # type: ignore  # pylint: disable=no-value-for-parameter
def job_documentation(job_name):
    if job_name != "run_completor":
        return None

    description = """Completor is a script for modelling
wells with advanced completion.
