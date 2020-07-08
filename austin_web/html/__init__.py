"""HTML resource handling utilities."""

from importlib_resources import files


def get_resource(name):
    return files("austin_web.html").joinpath(name).read_text()


def replace_references(text):
    """Replace {{ reference }} with the content of the referenced resource."""
    begin = 0
    while True:
        begin = text.find("{{", begin)
        if begin < 0:
            break
        end = text.find("}}", begin) + 2

        placeholder = text[begin:end]
        reference = placeholder[2:-2].strip()
        resource = get_resource(reference)

        text = text.replace(placeholder, replace_references(resource))

        begin += len(resource)

    return text


def replace_links(text):
    """Replace [[ link ]] with a link to the referenced resource."""
    begin = 0
    while True:
        begin = text.find("[[", begin)
        if begin < 0:
            break
        end = text.find("]]", begin) + 2

        placeholder = text[begin:end]
        reference = placeholder[2:-2].strip()
        link = "file://" + get_resource(reference)

        text = text.replace(placeholder, link)

        begin += len(link)

    return text


def load_site():
    template = get_resource("index.html")

    index = replace_links(replace_references(template))

    return index


if __name__ == "__main__":
    print(load_site())
