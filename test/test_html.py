import re

from requests import get

from austin_web.html import load_compile
from austin_web.html import load_site


URL_RE = re.compile(r"(?:src|href)=\"(http[s]*://[^\"]+)\"")


def fetch_cdn(url):
    response = get(url)
    assert response.status_code == 200


def test_load_site():
    site = load_site()
    assert "chart" in site

    for url in URL_RE.findall(site):
        fetch_cdn(url)


def test_load_compile():
    compile = load_compile("{test}", "Time")
    assert "var data = {test}" in compile
    assert "var label = time_label" in compile
    assert "Time Profile" in compile

    for url in URL_RE.findall(compile):
        fetch_cdn(url)
