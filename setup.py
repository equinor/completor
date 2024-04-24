#!/usr/bin/env python
"""Setup for completor packages"""

from glob import glob
from os.path import basename, splitext

import setuptools
from setuptools import find_packages

SSCRIPTS = ["completor = completor.main:main"]

REQUIREMENTS = [
    "matplotlib",
    "numpy<2",
    "pandas",
    "scipy",
    "Pillow>=10.0.1",  # not directly required, pinned to avoid a vulnerability
    "pydantic>=2.4.2",
    "wheel",
]

TEST_REQUIREMENTS = [
    "autoapi",
    "black",
    "check-manifest",
    "flake8",
    "pre-commit",
    "pytest",
    "pytest-cov",
    "rstcheck",
    "setuptools_scm",
    "promise",
]

DOCS_REQUIREMENTS = [
    "autoapi",
    "sphinx==6.2.1",
    "sphinx-argparse",
    "sphinx-autodoc-typehints",
    "sphinx_rtd_theme",
]

ERT_REQUIRMENTS = ["ert"]

EXTRAS_REQUIRE = {"tests": TEST_REQUIREMENTS, "docs": DOCS_REQUIREMENTS, "ert": ERT_REQUIRMENTS}

if __name__ == "__main__":
    setuptools.setup(
        name="completor",
        description="Completor",
        author="Equinor",
        author_email="opensource@equinor.com",
        url="https://github.com/equinor/completor",
        project_urls={"Issue Tracker": "https://github.com/equinor/completor/issues"},
        keywords="fmu, completor",
        license="Not open source (violating TR1621)",
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Developers",
            "Natural Language :: English",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
        ],
        platforms="any",
        include_package_data=True,
        packages=find_packages("completor"),
        package_dir={"": ""},
        python_requires=">=3.8",
        py_modules=[splitext(basename(path))[0] for path in glob("completor/*.py")],
        install_requires=REQUIREMENTS,
        setup_requires=["setuptools >= 28", "setuptools_scm", "pytest-runner"],
        entry_points={
            "console_scripts": SSCRIPTS,
            "ert": ["run_completor = completor.hook_implementations.jobs"],
        },
        # use_scm_version={"write_to": "completor/version.py"},
        test_suite="tests",
        extras_require=EXTRAS_REQUIRE,
        zip_safe=False,
    )
