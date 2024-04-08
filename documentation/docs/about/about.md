# COMPLETOR® Operational Runbook

This is the **Completor® Handbook**; aka Runbook. Completor® is open-source software, thus **the Completor® Runbook must NOT contain any secrets or restricted information**. Please help us keeping this document up-to-date and relevant. Make it more readable if something is unclear and propose corrections if something is wrong. Thanks!

# Product
| Product status      |                               |
|---------------------|-------------------------------|
| Life Cycle State    | NOW                           |
|  Operational Status | IN OPERATION                  |
|  Toolbox            | Dynamic Subsurface Assessment |


Completor® is a command line utility for generating input schedule files for Eclipse/OPM Flow,
representing wells with and without inflow control technology
(ICD and AICD, including DAR and AICV) and zonal isolation (optional).

Completor® reads a multi-segment input schedule file and a configuration `.case` file, specifying the completion design.
It combines the segment structure of the input schedule file with the completion design of the configuration file
and outputs a new schedule file to be included in an Eclipse/OPM Flow data file.

The input schedule file requires multi-segment well definitions from a pre-processing tool like RMS, ResInsight,
Petrel, Schedule etc. The completion configuration file is set up manually, with information from CSD or similar tools.
Requirements for the input schedule file, instruction on how to specify the completion design of the configuration file
and description on how to retrieve and define input parameters is found in [configuration.md](configuration.md). 
Useful examples are found in [examples.md](examples.md).

# Team

The Completor® team is a DevOps team, responsible for both development and operation (run & maintain) of Completor®.
The team is also responsible for 1st and 2nd line issue handling and customer support.
Completor® is one of several software deliveries from the Inflow Control Software team, 
which is a part of the Inflow Control team, with personnel from TDI OG SUB RPE (mainly domain competency) 
and TDI EDT DSD (mainly IT competency).

# User Support

## 1st line user support

A comprehensive user manual with technical details and useful examples on how to configure Completor is found in

TODO(#18): Replace link, see issue

[docs/getting_started](https://github.com/equinor/completor/blob/main/docs/getting_started).
Additionally, there is a memo describing how to implement [Completor in
FMU](https://statoilsrm.sharepoint.com/:w:/r/sites/WellBuilder/_layouts/15/Doc.aspx?action=edit&sourcedoc=%7B23A1CB42-6F18-4111-8C58-FF2A21A238C9%7D).

TODO(#19): Cannot access the link? Replace it?

Further questions and/or bug reports, general feature requests and improvement proposals may be conveyed by:

TODO(#20): Internal discussion forum?
- Yammer post to the [Inflow Control Technology community](https://web.yammer.com/main/groups/eyJfdHlwZSI6Ikdyb3VwIiwiaWQiOiI4NjI2OTE3Mzc2MCJ9/all).

Non-confidential questions and/or bug reports,
feature requests and improvement proposals may be posted at the Inflow Control Technology community.
Information about releases and release notes will also be notified to this community.

-   E-mail to the Completor® team at collective e-mail to [fg_InflowControlSoftware@equinor.com](fg_InflowControlSoftware@equinor.com).

The functional mail group is established for handling inquiries and issues related to inflow control modeling and 
simulation e.g. Completor® errors, improvement proposals and support, requests for inflow control modelling parameters,
plotting and analyzing simulation results with inflow control and questions related to any of the other software 
products developed and/or operated by the Inflow Control Software team, i.e. VaMoT® and/or ICV control.

-   Posting non-confidential questions at Teams channel: [Completor -\> General](https://teams.microsoft.com/l/channel/19%3a1fc110ba3bbc428db700b8e71c7c1620%40thread.skype/General?groupId=a0499e5f-0576-4bae-981d-3b2438eb014b&tenantId=3aa4a235-b6e2-48d5-9195-7fcf05b459b0) (for Equinor users only).

## 2nd line user support

A more in-depth and hands-on follow-up over time is arranged through ServiceNow at the [production technology service-now self-service](https://equinor.service-now.com/selfservice?id=sc_cat_item&sys_id=3cbd84e46f2d1100f582a8ff8d3ee448).
Select COMPLETOR from the list of applications, describe the scope,
assign a contact person, provide a WBS and add EPO task leader to the watch list.
The request will be discussed and coordinated internally in the Inflow Control team.
It will be assigned to a team member
who will follow-up on behalf of and in close collaboration with the Inflow Control team until the task is solved.

# Infrastructure

## Hosting

Completor® is hosted at GitHub for a collaborative and transparent approach to software development,
facilitating code review and version control.
A backlog of issues is managed in the [Completor project](https://github.com/equinor/completor/projects/1).

## Distribution

Within Equinor Completor® is installed on all Linux machines and accessible to internal users from the code distribution system [equinor/komodo](https://github.com/equinor/komodo).
To activate komodo and get the current stable version of Completor:

If you use cshell append `.csh` to the commands below.
```bash
source /prog/res/komodo/stable/enable
```

For unreleased (i.e., not stable) version check out:
```bash
source /prog/res/komodo/testing/enable
```

or for the daily updated, no-guarantees, bleeding edge:
```bash
source /prog/res/komodo/bleeding/enable
```

For installation on non-Equinor computers, create and activate a Python3 virtual environment and run:
TODO(#21): Update this documentation. It Should be more fleshed out for externals.
```bash
pip install git+https://github.com/equinor/completor
```

# Links/references

The basic framework for developing software in Equinor is specified in Software Development Principles.
Completor® is developed, run and maintained according to most of these principles.

-   Architecture contract [Completor.md](https://github.com/equinor/architecturecontract/pull/722) (currently PR, to be reviewed by Thorvald Johannessen, not yet merged into main).
-   [Architecture Diagram](https://ea.equinor.com/companyea/?oid=1cd67a86-59b3-40e0-81c0-fc9fe4bd108a).
    for Completor in QLM (established by Roy Tingstad, based on C1 and C2 diagrams established by Øyvind Kvalnes in collaboration with Completor DevOps team).
-   [Enterprise Architecture](https://ea.equinor.com/companyea/?oid=1cd67a86-59b3-40e0-81c0-fc9fe4bd108a) established by Roy Tingstad (in collaboration with Completor® DevOps team).

# Operational Guidelines

## Preparation/competency/requirements

Some training is recommended or mandatory to establish a GitHub user and contribute to the Equinor software portfolio.
Please refer to [Equinor University](http://learning.equinor.com/) and sign up for the following courses:

-   \[TR_DIGI\] Equinor Software Developer Onboarding.
-   \[TR_FUNC\] Code of Conduct e-learning.
-   \[DIGI\] IT Rules.

TODO(#23): Cant find the two following courses.
-   \[TR_DIGI\] Cyber Security: Basic.
-   \[TR_DIGI\] Cyber Security: Advanced.

## Communication

-   GitHub may be used for general comments related to issues/reviews.
-   Slack has a (currently private) [\#completor](https://equinor.slack.com/archives/C02MVVAC9L4) channel for developers/contributors (ask for access).
-   [Inflow Control Technology community](https://web.yammer.com/main/groups/eyJfdHlwZSI6Ikdyb3VwIiwiaWQiOiI4NjI2OTE3Mzc2MCJ9/all) at Yammer may be used for questions, bug reports, feature requests and improvement proposals.
-   E-mail group [fg_InflowControlSoftware@equinor.com](fg_InflowControlSoftware@equinor.com) is used for issue tracking and customer support.

## Contributions

Contributions in terms of code, bug reports and/or feature requests are welcome.
Please refer to the developer manual for an overview of the code base.

[//]: # (The developer manual may be cloned to any unix directory and built to html format by running .)
For more information about prerequisites, code conventions,
routines for release and deployment, testing, recovery, logging,
and monitoring, the reader is referred to paragraph [Operational Guidelines](#operational-guidelines).

### Legal terms and conditions for contributions

Any contributions will undergo review before they are (potentially) accepted.
Completor® is deployed under copy-left license GPLv3,
which implies that any contributions will be merged under the same license.
Equinor originally has 100% ownership of Completor®.
If external contributions are accepted, the ownership will be distributed between Equinor and the contributors.
Only contributions not transferring copyright may be accepted.
Equinor will attempt to respond to bug reports and improvement proposals,
but Equinor is not liable for maintenance on behalf of external users.

### Practical instructions on how to contribute

Issues may be reported directly on the Completor Issue Board.
The issue board reflects the status of the issue handling.
The status of the issue is not updated by moving issues between lanes in the board.
Please refer to [Linking a pull request to an issue](https://docs.github.com/en/free-pro-team@latest/github/managing-your-work-on-github/linking-a-pull-request-to-an-issue) 
for instructions on how pull requests are linked to issues at GitHub.

Alternatively,
issues may be reported to the DevOps team at Yammer([Inflow Control Technology community](https://web.yammer.com/main/groups/eyJfdHlwZSI6Ikdyb3VwIiwiaWQiOiI4NjI2OTE3Mzc2MCJ9/all)),
via the [\#completor](https://equinor.slack.com/archives/C02MVVAC9L4) channel at Slack (non-public,
apply for access) or by e-mail to the Inflow Control Software team (comprising the Completor® team)
at [fg_InflowControlSoftware@equinor.com](fg_InflowControlSoftware@equinor.com).
Issues reported to the DevOps team will be added to the backlog for follow-up.

## Getting started as a developer

**Getting access to GitHub**

Access to the Equinor domain at GitHub is obtained through AccessIT.
Generate a user account at GitHub.
Equinor is a "Single Sign-on Organization" so keys are required to be authorized for access.
Create an SSH key under settings/SSH and GPG keys.
Check out the GitHub guide on how to generate the SSH keys at the same location.

**Python virtual environment**

After cloning, you need a Python virtual environment in which you install completor and its dependencies.
If you develop on an Equinor computer you should use `komodoenv` as outlined above.

**Setting up a private komodo Python environment**

A private komodo Python environment is needed for the following reasons:

-   Running the local version of the Completor code instead of the stable version in komodo.
-   Running tests on the local Completor version.
-   Installing code and dependencies that are needed for maintaining the Completor code without breaking the stable komodo installation.

The need for extending a komodo environment is supported by using komodoenv.
The following describes how to use it:

1.  Activate any komodo release that includes komodoenv (any komodo-release from 2020.11 and onwards). Example: `source /prog/res/komodo/stable/enable`
2.  Run the command komodoenv -r \<release\> monty, where \<release\> is
    replaced by the name of the release you want to extend.
    This will create a virutal environment named monty in the current directory.
    Currently \<release\> needs to point to a specific release (eg.
    2020.11.00-py36), but in the future specifying named releases such as stable will be supported.
3.  Activate the environment by running source monty/enable.csh, and you are now ready to install packages using pip!
4.  Note that you may have to revert to komodo/stable when finished with Completor updates.
    E.g. for running FMU that requires updated komodo/stable utilities.
5.  As the private komodo environment is linked to a specific komodo release, please update or create a new private environment when komodo is updated.

Equinor Komodo Usage — Equinor Komodo Release 1.0 documentation

### Installing Completor in the private environment

Make sure the private environment is activated with step 3 above.

```bash
python3 -m venv venv
source venv/bin/activate
```

and then install:

```bash
pip install -e ".[tests,docs]"
```

This will install the local version of Completor in editable-mode, all dependencies, test suites and documentation.
Exiting (source to /prog/res/komodo/stable/enable) and entering environment may be required for to realize that new functionality has been added.

A good start is to verify that all tests pass after having cloned the repository:
``` console
pytest .
```

**Forking Completor**

The first thing to do, is to create a fork of completor to your personal GitHub account. 
Go to [https://github.com/equinor/completor](https://github.com/equinor/completor) and click the "Fork" button.
Clone your fork to your local computer:

``` console
git clone git@github.com:<youraccount>/completor
cd completor
```

Then add the upstream repository:

``` console
git remote add upstream git@github.com:equinor/completor
```

This requires a valid login setup with SSH keys for your GitHub account, needed for write access.

**Creating your own branch**

Create a new branch to start working on your changes/amendments:

```bash
git checkout -b "branch-name" \# Creates a new branch from main
```

useful to check if everything is OK:

```bash
git status
```

**Editing and updating files**

Edit your files and tell git that you want to do updates by:

```bash
git add \<files\> \#Adds new files to the branch
```

When you're done editing, tell git you are done:

```bash
git commit -m 'some description here, please'
```

The git add and git commit commands can be combined in git commit -am
'some description'

Before pushing the changes to GitHub, make sure that all items in the
Workflow Section below are covered.

Finally push it to the GitHub repo (in our case to the
branch-name-branch):

```bash
git push origin branch-name
```

Check if your files are in sync with repo:

```bash
git remote show origin
```

Result would then be (at the end):

Local refs configured for 'git push':  
branch pushes to branch (up to date) main pushes to main (up to date)

**Updating your branch with the latest code version before editing:**

If you want to edit your branch at a later stage, make sure you have all
the updates from other developers before editing on your own branch, by
typing:

```bash
git checkout main
git pull origin main
```

Then create the branch with git checkout -b "branch-name".

**GitHub workflow**

For all edits to any file at GitHub you will be prompted with a request
to create a PR (pull request) with the branch-name that was recently
pushed. 1. To make a PR, click the prompt and give a description of the
changes. 2. Wait to see if all tests are passed at GitHub 3. In the
menues to the right, associate the PR with an existing issue. Issues are
decribed in the issue list. 4. Add a reviewer in the menu to the right.
5. When review is approved: Squash and merge the branch into the main
repo with a text describing what the change/amendment does.

## Building developer documentation

[//]: # (Run a build of the developer documentation locally before uploading to)

[//]: # (GitHub. The command for this is found at the end of the file .travis.yml)

[//]: # (at \~/subscript-internal/)

[//]: # ()
[//]: # (> sphinx-build -W -b html -nv docs/ build/docs)

[//]: # ()
[//]: # (Alternatively, the docs can be checked using the second to last command)

[//]: # (in the .travis.yml file)

[//]: # ()
[//]: # (> rstcheck -r docs)

[//]: # ()
[//]: # (If the code passes these tests and checks, proceed with upload to)

[//]: # (GitHub.)

## Repository conventions

-   Use `setup.py` for installing endpoints that users should have in
    their `$PATH`.
-   Use `argparse`, and with a specific `get_parser()` function to
    facilitate `sphinx-argparse`.
-   Docstrings on all functions. Docstrings can include RST formatting
    and will be checked for compliance with sphinx on every pull
    request. Warnings from sphinx must be fixed.

# Code style 

TODO: Check if information is correct and relevant.

-   PEP8 is the rule for naming of files, functions, classes, etc.
    Exception to PEP8 is maximum width at 120 instead of PEP8's 79.
-   Use `pre-commit` to enforce compliance before commit.
    Pre-commit is part of the test requirements,
    see section [Installing Completor in the private environment](#Installing-Completor-in-the-private-environment). 
    Run `pre-commit install` in the repository root after you've gotten the test-requirements.
    This will save you from pushing code that will fail the code style tests required before merge.
    These rules include but are not limited to:
    -   Black - formatter.
    -   Flake8 - linter.
    -   Mypy - static type checking.
    -   Isort - sorting of import statements.

Pre-commit is triggered to run all these checks and more when running `git commit`.
To manually trigger a check you can run it by calling `pre-commit run --all`.
To run certain hooks individually against certain files run `pre-commit run tool-name filepath`.

[//]: # (- Use pylint to improve coding.)
[//]: # (    -   `pip install pylint`.)
[//]: # (    -   Then run `pylint src`.)
[//]: # (    -   Deviations from default &#40;strict&#41; pylint are stored in `.pylintrc` at root level, or as comments in the file e.g. `# pylint: disable=broad-except`.)
[//]: # (    -   Only use deviations when e.g. black and pylint are in conflict, or if conformity with pylint would clearly make the code worse or not work at all. Do not use it to increase pylint score.)

## Release & Deployment

The PETEC Reservoir Toolbox is responsible for the release of Komodo.
Refer to [\#komodo-maintainers](https://equinor.slack.com/archives/CKC3ST0UT) at Slack for feature freeze dates and procedures for release to komodo.
Release notes are found at [https://github.com/equinor/completor/releases](https://github.com/equinor/completor/releases).

## Testing

**Automatic code tests** TODO: Check if information on "Automatic code
tests" is correct and relevant.

Every change or addition to the code shall be followed by one or more tests verifying the intended update change.
Most modules have already a set of tests located in \~/subscript-internal/tests/completor/ The program pytest is used
to verify the tests.
All tests must be checked with pytest and pass before uploading to GitHub.
The same tests are run at GitHub and the upload will fail if a test fails.

To run all tests:

```bash
pytest tests/
```

To run a specific test (test_perf) in a test file:

```bash
pytest tests/completor/test_main.py::test_perf
```

[https://docs.pytest.org/en/](https://docs.pytest.org/en/)

### Automatic Test Gates

-   On commit, code is automatically formatted, with pre-commit git hooks.
-   On every push to a branch/repository, the continuous integration (CI) pipeline ensures that the code is built,
    and automatic tests are run.
    The testing includes integration and unit tests and automatic checks for security vulnerabilities, and licensing.

### Manual Test Gates

-   Manual testing by the DevOps team. If we break it, we fix it ASAP.
-   Quality Assurance: Manual testing by users. Patched until approved by user.
-   Production: Weekly meetings to handle bug reports, feature requests and improvement proposals from users.
    When approved by CAB (user representatives, DevOps team, PO, Toolbox owner?), the release can be pushed to Komodo.
-   Currently manual release tests. Ask Komodo team to include release tests for Completor® in Komodo workflow (#166).

## (Disaster) Recovery

If Completor® breaks, the issue is handled in collaboration between user, DevOps team and PO.
In case of urgency, the user can source an operative version of Completor® from Komodo until the issue is solved.
In case of a Komodo disaster, the repository to which Completor® is deployed can be cloned from GitHub.
Check out specific commit hash.

## Logging and Monitoring

Some incidents generate an error message including a zip-file
to be sent as attachment to the DevOps team at [fg_InflowControlSoftware@equinor.com](fg_InflowControlSoftware@equinor.com) for follow-up.
(Not automatic, to avoid conflict with GDPR).
The zip-file contains the Completor® include files and an error log.
The code is also monitored by the CI process (could be configured for daily testing and reporting).
Dependabot is activated for automatic warning about vulnerabilities in dependencies.
Additionally, the Completor® code provides the user with an option to set loglevel (verbosity) when running Completor®.
