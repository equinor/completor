# Completor®
Completor® is an Equinor developed Python Command Line Interface (CLI) for modeling wells with inflow control technology.

## Introduction
Completor® reads the multi-segmented tubing definition generated by reservoir modelling pre-processing tool and a user defined file (called "case" file) specifying the completion design.
The information in the input schedule file and the case file is combined
and written to a new schedule file to be included in your reservoir simulator.

## Documentation
Detailed documentation for usage of completor can be found at https://equinor.github.io/completor.

## Getting started as a user

### Prerequisites
* [Python](https://www.python.org/), version 3.11
* [ERT](https://github.com/equinor/ert) (optional, and only available on Linux.)

### Installation
To start using Completor®, you can follow these instructions:

```shell
git clone https://github.com/equinor/completor.git
cd completor
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

If you intend to run completor as a plugin to ert:
```shell
git clone https://github.com/equinor/completor.git
cd completor
python -m venv venv
source venv/bin/activate
pip install -e ".[ert]"
```

Ensure it runs as intended, confirm it with:
```shell
completor --help
```
This should run for some time and display a help message.

### Create and run your first model
Some examples of Completor case file are available in [Examples](documentation/docs/about/examples.mdx) and detailed explanation is available in [Configuration](documentation/docs/about/configuration.mdx).

## Getting started as a contributor
### Contribution guide
We welcome all kinds of contributions, including code, bug reports, issues, feature requests, and documentation.
The preferred way of submitting a contribution is to either make an issue on GitHub or by forking the project on GitHub
and making a pull request.

See [Contribution Document](documentation/docs/contribution_guide.mdx) on how to contribute.

### Install completor as dev
In order to run Completor® you need to have versions of [Python 3.8 to 3.11](https://www.python.org/downloads/) installed.
#### Source code
Clone the [Completor® repository](https://github.com/equinor/completor) to get the source code.
```bash
git clone https://github.com/equinor/completor.git
cd completor
```

#### Pipx
[Install pipx](https://github.com/pypa/pipx#install-pipx), although it's optional next step assumes pipx is installed, check poetry docs for other installation options.

Linux:
```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```
Windows:
```bash
python -m pip install --user pipx
# replace python with python3 if installed from Windows app store.
```
Mac:
```bash
brew install pipx
pipx ensurepath
```

#### Install Poetry:
For options other than pipx see [poetry documentation](https://python-poetry.org/docs/main/#installation)
Open a new terminal/tab then
```bash
pipx install poetry
```
Let Poetry install all dependencies for you.
```bash
poetry install
```
If you're in a Linux environment add the extra Ert dependencies!
```bash
poetry install -E ert
```

Activate poetryenv (or use venv if that is more familiar, poetry should respect it as an environment):
```bash
poetry shell
```

Now you should be able to check that everything is installed correctly by running
```bash
pytest
```
in the activated poetry shell.

Information regarding integration with PyCharm can be found here: https://www.jetbrains.com/help/pycharm/poetry.html#poetry-env
More info on viewing your environment information can be found here: https://python-poetry.org/docs/managing-environments/#switching-between-environments

Poetry support completion scripts for Bash, Fish and Zsh [detailed information can be found here](https://python-poetry.org/docs/#installing-with-pipx).

#### Pre-commit

This project makes use of pre-commit to ensure commits adhere to certain rules and standards.
Pre-commit should already be installed in the `poetry install` command, but you need to activate the hooks like so:
```bash
pre-commit install
```

If for some reason this is not working correctly you can install pre-commit separately like this:
```bash
pipx install pre-commit
pre-commit install
```

Now pre-commit should be a constant nuisance, bothering you with some minor change each time you want to commit.
Although annoying this is preferable to having lots of minor quirks in the code, such as trailing whitespace everywhere.
Just run git commit a second time, remembering to add the changes made by pre-commit and you should be mostly good!

> Git hook scripts are useful for identifying simple issues before submission to code review.
> Run hooks on every commit to automatically point out issues in code such as missing semicolons, trailing whitespace, and debug statements.
> By pointing these issues out before code review, this allows a code reviewer to focus on the architecture of a change while not wasting time with trivial style nitpicks.
> Black will style your code automatically to match the Black code style, and Flake8 will check your code for style, syntax, and logical errors.
> Remember to add the changes made by the scripts to your commit.

#### Running unit- and integration tests

This project uses [pytest](https://docs.pytest.org/en/stable/) for unit and integration testing.
Run it before every push to make sure your code is working as intended.
To run all tests discovered by pytest, run the following command when in the root folder

Recommended settings/launch args:
This makes the tests run in parallel and in turn go a bit more brrrr.
```bash
pytest -n auto
```

### Versioning
This project make use of [Release Please](https://github.com/googleapis/release-please) to keep track of versioning.
By following [conventional commit messages](https://www.conventionalcommits.org/en) (enforced) in PR titles, and squash-merging, the release please workflow will automatically create/update release-PRs based on which change is performed.

### Black and Flake8
This project uses [Black](https://pypi.org/project/black/) and [Flake8](https://pypi.org/project/flake8/) for code formatting and linting.
It deviates from the default black config by setting the max line length to 120 characters.

It might be helpful turn on format-on-save, and make black format your code on save.

A helpful visual aid is to set rulers in your editor to 120 characters.
Code should not exceed 120 characters.
Add this to you `settings.json` to set rulers in VSCode:

```json
{
  "editor.rulers": [
    120
  ],
  "workbench.colorCustomizations": {
    "editorRuler.foreground": "#33779944"
  }
}
```
