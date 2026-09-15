from xml.dom import minidom
from xml.dom.minidom import Text


def element_text(node: minidom.Document | minidom.Element, tag: str) -> str:
    first_child = node.getElementsByTagName(tag)[0].firstChild
    if not isinstance(first_child, Text):
        raise AssertionError(f"<{tag}> element has no text content")
    return first_child.data
