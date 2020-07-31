from austin.cli import AustinCommandLineError
from austin_web.__main__ import _main, AustinWeb
from pytest import raises


def test_compile_serve():
    with raises(AustinCommandLineError):
        _main(AustinWeb, ["--compile", "foo", "--serve"])
