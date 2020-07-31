"""HTML resource handling utilities."""

from typing import Optional, Tuple

from importlib_resources import files


def get_resource(name: str) -> str:
    """Load a resource file from the submodule ``austin_web.html``."""
    return files("austin_web.html").joinpath(name).read_text(encoding="utf-8")


def _find_marker(
    text: str, ldel: str, rdel: str, begin: int
) -> Optional[Tuple[int, int, str]]:
    begin = text.find(ldel, begin)
    if begin < 0:
        return None
    end = text.find(rdel, begin) + len(rdel)

    return begin, end, text[begin:end]


def replace_references(text: str) -> str:
    """Replace {{ reference }} with the content of the referenced resource."""
    begin = 0
    while True:
        marker = _find_marker(text, "{{", "}}", begin)
        if not marker:
            break

        begin, end, placeholder = marker

        reference = placeholder[2:-2].strip()
        resource = get_resource(reference)

        text = text.replace(placeholder, replace_references(resource))

        begin += len(resource)

    return text


def replace_links(text: str) -> str:
    """Replace [[ link ]] with a link to the referenced resource."""
    begin = 0
    while True:
        marker = _find_marker(text, "[[", "]]", begin)
        if not marker:
            break

        begin, end, placeholder = marker

        reference = placeholder[2:-2].strip()
        link = "file://" + get_resource(reference)

        text = text.replace(placeholder, link)

        begin += len(link)

    return text


def replace_placeholders(text: str, **kwargs: str) -> str:
    """Replace occurrences of ((% placeholder %)) with the given keyword arguments."""
    if not kwargs:
        return text

    begin = 0
    while True:
        marker = _find_marker(text, r"((%", r"%))", begin)
        if not marker:
            break

        begin, end, placeholder = marker

        key = placeholder[3:-3].strip()
        value = kwargs.get(key)

        if not value:
            begin += 3
            continue

        text = text.replace(placeholder, value)

        begin += len(value)

    return text


def _load_and_resolve_resource(name: str, **kwargs: str) -> str:
    return replace_placeholders(
        replace_links(replace_references(get_resource(name))), **kwargs
    )


def load_site() -> str:
    """Load the site index page."""
    return _load_and_resolve_resource("index.html")


def load_compile(data: str, profile_type: str) -> str:
    """Load the compiler page.

    The ``data`` string argument is a serialised JSON object. The
    ``profile_type`` should be either ``Time`` or ``Memory``.
    """
    return _load_and_resolve_resource(
        "austin_web.html",
        data=data,
        profile_type=profile_type,
        label=profile_type.lower(),
    )
