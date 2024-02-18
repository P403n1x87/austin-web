from austin.cli import AustinCommandLineError
from pytest import raises

from austin_web.__main__ import AustinWeb
from austin_web.__main__ import _main


def test_compile_serve():
    with raises(AustinCommandLineError):
        _main(AustinWeb, ["--compile", "foo", "--serve"])
