import tempfile

import nox


nox.options.sessions = "lint", "tests"


# ---- Configuration ----


SUPPORTED_PYTHON_VERSIONS = ["3.6", "3.7", "3.8", "3.9"]

PYTEST_OPTIONS = ["-vvvs", "--cov=austin_web", "--cov-report", "term-missing"]

LINT_LOCATIONS = ["austin_web", "test", "noxfile.py"]
LINT_EXCLUDES = []

MYPY_LOCATIONS = LINT_LOCATIONS[:1]


# ---- Helpers ----


def install_with_constraints(session, *args, **kwargs):
    with tempfile.NamedTemporaryFile() as requirements:
        session.run(
            "poetry",
            "export",
            "--dev",
            "--format=requirements.txt",
            f"--output={requirements.name}",
            external=True,
        )
        session.install(f"--constraint={requirements.name}", *args, **kwargs)


# ---- Sessions ----


@nox.session(python=SUPPORTED_PYTHON_VERSIONS)
def tests(session):
    session.run("poetry", "install", "-vv", external=True)
    session.run("poetry", "run", "python", "-m", "pytest", *PYTEST_OPTIONS)


@nox.session(python=SUPPORTED_PYTHON_VERSIONS)
def lint(session):
    session.install(
        "flake8",
        "flake8-annotations",
        "flake8-bugbear",
        "flake8-docstrings",
        "flake8-import-order",
    )
    session.run("flake8", *LINT_LOCATIONS)  # , "--exclude", *LINT_EXCLUDES)


@nox.session(python=SUPPORTED_PYTHON_VERSIONS)
def mypy(session):
    session.install("mypy")
    session.run("mypy", *MYPY_LOCATIONS)


@nox.session(python="3.7")
def coverage(session):
    """Upload coverage data."""
    install_with_constraints(session, "coverage[toml]", "codecov")
    session.run("coverage", "xml", "--fail-under=0")
    session.run("codecov", *session.posargs)
