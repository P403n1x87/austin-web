"""HTML resource handling utilities."""

from importlib_resources import files


def get_resource(name):
    return files("austin_web.html").joinpath(name).read_text()


def _find_marker(text, ldel, rdel, begin):
    begin = text.find(ldel, begin)
    if begin < 0:
        return None
    end = text.find(rdel, begin) + len(rdel)

    return begin, end, text[begin:end]


def replace_references(text):
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


def replace_links(text):
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


def replace_placeholders(text, **kwargs):
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


def _load_and_resolve_resource(name, **kwargs):
    return replace_placeholders(
        replace_links(replace_references(get_resource(name))), **kwargs
    )


def load_site():
    return _load_and_resolve_resource("index.html")


def load_compile(data, profile_type):
    return _load_and_resolve_resource(
        "austin_web.html",
        data=data,
        profile_type=profile_type,
        label=profile_type.lower(),
    )


if __name__ == "__main__":
    print(load_site())
