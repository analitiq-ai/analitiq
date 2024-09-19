"""Nox config file, no issues known."""

# pylint: disable=line-too-long
import nox

nox.options.sessions = (
    "install",  # this is mandatory to ensure, that all needed modules are installed by poetry first
    "ruff_format",
    "ruff_check",
    "pylint",
    "mypy",
    "pytest",
    "pytest_e2e",
    # "coverage",
)
locations = "libs/analitiq", "libs/tests", "noxfile.py"


@nox.session(python=False)
def install(session):
    """Install dependencies."""
    session.run("poetry", "install")


@nox.session(python=False)
def ruff_format(session):
    """Run ruff code formatter."""
    args = session.posargs or locations
    session.run("ruff", "format", *args)


@nox.session(python=False)
def ruff_check(session):
    """Run ruff linter."""
    args = session.posargs or locations
    session.run("ruff", "check", *args)


@nox.session(python=False)
def safety(session):
    """Run safety."""
    session.run(
        "poetry",
        "export",
        "--with dev",
        "--format=requirements.txt",
        "--without-hashes",
        "--output=requirements.txt",
        external=True,
    )
    session.run("safety", "check", "--file=requirements.txt", "--full-report")


@nox.session(python=False)
def pylint(session):
    """Run pylint."""
    args = session.posargs or locations
    session.run("pylint", "--output-format=text", "--fail-under=8", *args)


@nox.session(python=False)
def mypy(session):
    """Run mypy."""
    args = session.posargs or locations
    session.run("mypy", "--namespace-packages", *args)


@nox.session(python=False)
def pytest(session):
    """Run pytest."""
    session.run(
        "pytest",
        "--timeout=60",
        "--capture=sys",
        "--junitxml=pytest-report.xml",
        "--cov=libs/analitiq",
        # "--cov-fail-under=80",
        # "--cov-omit=src/demo/*",
        "libs/tests/unit/",
        # "--ignore=tests/unit/demo",
    )  # in order to see output to stdout set: --capture=tee-sys


@nox.session(python=False)
def coverage(session):
    """Run coverage."""
    session.run("coverage", "xml", "-o", "coverage-python.xml")


@nox.session(python=False)
def pytest_o(session):
    """Run pytest with tee-sys."""
    session.run(
        "pytest",
        "--capture=tee-sys",
        "tests/",
    )


@nox.session(python=False)
def pytest_integration(session):
    """Run pytest with integration tests only."""
    session.run(
        "pytest",
        "--timeout=15",
        "--capture=sys",
        "libs/tests/integration/",
    )  # in order to see output to stdout set: --capture=tee-sys


@nox.session(python=False)
def pytest_e2e(session):
    """Run pytest with e2e tests only."""
    session.run(
        "pytest",
        "--timeout=15",
        "--capture=sys",
        "libs/tests/e2e/",
    )  # in order to see output to stdout set: --capture=tee-sys
