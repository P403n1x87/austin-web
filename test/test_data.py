from austin_web.data import WebFrame


def test_webframe():
    root = WebFrame.new_root()

    root += WebFrame.parse("P123;T0:0x546745146 1042")

    assert root.height == 3

    root += WebFrame.parse(
        "P123;T0:0x546745146;foo_module.py:foo:10;bar_module.py:bar:20 1042"
    )

    node = root
    for height in range(5, 0, -1):
        assert node.height == height
        node = node.children[0] if node.children else None
