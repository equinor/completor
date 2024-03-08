#!/usr/bin/env python
"""Setup for completor packages"""
from __future__ import annotations

from glob import glob
from os.path import basename, splitext

import setuptools
from setuptools import find_packages

SSCRIPTS = ["completor = completor.main:main"]

LEGACYSCRIPTS: list[str] = []

REQUIREMENTS = [
    "matplotlib",
    "numpy<2",
    "pandas",
    "scipy",
    "ert",
    "Pillow>=10.0.1",  # not directly required, pinned to avoid a vulnerability
    "pydantic>=2.4.2",
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

EXTRAS_REQUIRE = {"tests": TEST_REQUIREMENTS, "docs": DOCS_REQUIREMENTS}

if __name__ == "__main__":
    setuptools.setup(
        name="completor",
        description="Completor",
        author="Equinor",
        author_email="fg_InflowControlSoftware@equinor.com",
        url="https://github.com/equinor/completor",
        project_urls={
            "Documentation": "https://fmu-docs.equinor.com/docs/completor",
            "Issue Tracker": "https://github.com/equinor/completor/issues",
        },
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
        packages=find_packages("src"),
        package_dir={"": "src"},
        python_requires=">=3.8",
        py_modules=[splitext(basename(path))[0] for path in glob("src/*.py")],
        install_requires=REQUIREMENTS,
        setup_requires=["setuptools >= 28", "setuptools_scm", "pytest-runner"],
        entry_points={
            "console_scripts": SSCRIPTS,
            "ert": ["run_completor = completor.hook_implementations.jobs"],
        },
        scripts=["src/completor/legacy/" + scriptname for scriptname in LEGACYSCRIPTS],
