import shutil
from os import path
from pathlib import Path

import pytest

SKIP_TESTS = False
try:
    from ert.plugins.plugin_manager import ErtPluginManager # type: ignore
    import completor.hook_implementations.jobs_new as jobs
except ModuleNotFoundError:
    import platform

    if platform.system() == "Linux":
        raise ImportError(
            "Ert should be installed when on Linux OS."
            "Try installing with ERT `pip install 'completor[ert]'`!"
            "If you're developing try `poetry install -E ert` instead."
        )
    SKIP_TESTS = True

EXPECTED_JOBS = {"run_completor"}

from completor.hook_implementations import RunCompletor

@pytest.mark.requires_ert
def test_that_installable_fm_steps_work_as_plugins():
    """Test that the forward models are included as ERT plugin."""
    fms = ErtPluginManager(plugins=[jobs]).forward_model_steps

    assert RunCompletor in fms
    assert len(fms) == len(EXPECTED_JOBS)


@pytest.mark.requires_ert
def test_hook_implementations():
    """Test hook implementation."""
    pma = ErtPluginManager(plugins=[jobs])
    installable_fm_step_jobs = [fms().name for fms in pma.forward_model_steps]
    assert set(installable_fm_step_jobs) == set(EXPECTED_JOBS)

    expected_workflow_jobs = {}
    installable_workflow_jobs = pma.get_installable_workflow_jobs()
    for wf_name, wf_location in expected_workflow_jobs.items():
        assert wf_name in installable_workflow_jobs
        assert installable_workflow_jobs[wf_name].endswith(wf_location)

    assert set(installable_workflow_jobs.keys()) == set(expected_workflow_jobs.keys())


@pytest.mark.requires_ert
@pytest.mark.integration
def test_executables():
    """Test executables listed in job configurations exist in $PATH"""
    pma = ErtPluginManager(plugins=[jobs])
    for fm_step in pma.forward_model_steps:
        # the executable should be equal to the job name, but in lowercase letter
        assert shutil.which(fm_step().executable)




@pytest.mark.requires_ert
def test_hook_implementations_job_docs():
    """Testing hook job docs."""
    pma = ErtPluginManager(plugins=[jobs])

    for fm_step in pma.forward_model_steps:
        fm_step_doc = fm_step.documentation()
        assert fm_step_doc.description is not None
        assert fm_step_doc.category == "modelling.reservoir"