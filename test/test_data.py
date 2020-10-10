from austin_web.data import WebFrame


def test_webframe():
    root = WebFrame.new_root()

    root += WebFrame.parse("P123;T0x546745146 1042")

    assert root.height == 3

    root += WebFrame.parse(
        "P123;T0x546745146;foo (foo_module.py:10);bar (bar_module.py:20) 1042"
    )

    node = root
    for height in range(5, 0, -1):
        assert node.height == height
        node = node.children[0] if node.children else None
