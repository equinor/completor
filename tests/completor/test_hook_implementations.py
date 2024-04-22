import shutil
from os import path
from pathlib import Path

import pytest
import rstcheck_core.checker  # type: ignore

SKIP_TESTS = False
try:
    from ert.shared.plugins.plugin_manager import ErtPluginManager  # type: ignore

    import completor.hook_implementations.jobs
except ModuleNotFoundError:
    import platform

    if platform.system() == "Linux":
        raise ImportError("Ert should be installed when on Linux OS. Try pip installing like `pip install '.[ert]'`!")
    SKIP_TESTS = True

# pylint: disable=redefined-outer-name


@pytest.fixture
def expected_jobs():
    """dictionary of installed jobs with location to config"""
    expected_job_names = ["run_completor"]
    return {
        name: path.join(path.dirname(completor.__file__), "completor/config_jobs", name) for name in expected_job_names
    }


# Avoid category inflation. Add to this list when it makes sense:
ACCEPTED_JOB_CATEGORIES = ["modelling", "utility"]


@pytest.mark.skipif(SKIP_TESTS, reason="Skip these tests while developing outside of Linux environment.")
def test_hook_implementations(expected_jobs):
    """Test that we have the correct set of jobs installed,
    nothing more, nothing less"""
    plugin_m = ErtPluginManager(plugins=[completor.hook_implementations.jobs])

    installable_jobs = plugin_m.get_installable_jobs()
    for wf_name, wf_location in expected_jobs.items():
        assert wf_name in installable_jobs
        assert str(installable_jobs[wf_name]).endswith(wf_location)
        assert path.isfile(installable_jobs[wf_name])

    assert set(installable_jobs.keys()) == set(expected_jobs.keys())

    expected_workflow_jobs = {}
    installable_workflow_jobs = plugin_m.get_installable_workflow_jobs()
    for wf_name, wf_location in expected_workflow_jobs.items():
        assert wf_name in installable_workflow_jobs
        assert installable_workflow_jobs[wf_name].endswith(wf_location)

    assert set(installable_workflow_jobs.keys()) == set(expected_workflow_jobs.keys())


@pytest.mark.skipif(SKIP_TESTS, reason="Skip these tests while developing outside of Linux environment.")
def test_job_config_syntax(expected_jobs):
    """Check for syntax errors made in job configuration files"""
    for _, job_config in expected_jobs.items():
        # Check (loosely) that double-dashes are enclosed in quotes:
        for line in Path(job_config).read_text(encoding="utf8").splitlines():
            if not line.strip().startswith("--") and "--" in line:
                assert '"--' in line and " --" not in line


@pytest.mark.integration
@pytest.mark.skipif(SKIP_TESTS, reason="Skip these tests while developing outside of Linux environment.")
def test_executables(expected_jobs):
    """Test executables listed in job configurations exist in $PATH"""
    for _, job_config_file in expected_jobs.items():
        job_configuration_lines = [
            line
            for line in Path(job_config_file).read_text(encoding="utf8").splitlines()
            if line and not line.startswith("--")
        ]
        job_configuration = {line.split()[0]: "".join(line.split()[1:]) for line in job_configuration_lines}
        assert shutil.which(job_configuration["EXECUTABLE"])


@pytest.mark.skipif(SKIP_TESTS, reason="Skip these tests while developing outside of Linux environment.")
def test_hook_implementations_job_docs():
    """For each installed job, we require the associated
    description string to be nonempty, and valid RST markup"""

    plugin_m = ErtPluginManager(plugins=[completor.hook_implementations.jobs])

    installable_jobs = plugin_m.get_installable_jobs()

    docs = plugin_m.get_documentation_for_jobs()

    assert set(docs.keys()) == set(installable_jobs.keys())

    for job_name in installable_jobs.keys():
        desc = docs[job_name]["description"]
        assert desc != ""
        assert not list(rstcheck_core.checker.check_source(desc))
        category = docs[job_name]["category"]
        assert category != "other"
        assert category.split(".")[0] in ACCEPTED_JOB_CATEGORIES
