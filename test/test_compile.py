import os.path
from tempfile import TemporaryDirectory as TempDir

from austin_web.__main__ import _main, AustinWeb


def test_compile():
    with TempDir() as tempdir:
        tempfile = os.path.join(tempdir, "austin.html")
        _main(AustinWeb, ["--compile", tempfile, "python", "test/target.py"])
        with open(tempfile, "r") as fin:
            data = fin.read()
            assert "chart" in data
            assert "target.py" in data
