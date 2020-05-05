# from .checks import check_extract_article
from bs4 import BeautifulSoup
from ..readabilipy import simple_json_from_html_string
from ..readabilipy.simplifiers import normalise_text
from ..readabilipy.simple_json import plain_element, plain_text_leaf_node, add_node_indexes, content_digest


def test_empty_page():
    """Empty pages should return an empty <div>."""
    html = ""
    parsed_content = simple_json_from_html_string(html)
    assert parsed_content["content"] == "<div></div>"


def test_contentless_page():
    """Contentless pages should return an empty <div>."""
    html = "<html></html>"
    parsed_content = simple_json_from_html_string(html)
    assert parsed_content["content"] == "<div></div>"


def test_plain_element_with_comments():
    """Contents of comments should be stripped but the comment itself should be kept."""
    html = """
        <div>
            <p>Text</p>
            <!-- comment -->
        </div>
    """.strip()
    soup = BeautifulSoup(html, 'html.parser')
    elements = [str(plain_element(element, False, False)) for element in soup.contents]
    assert elements == ["<div><p>Text</p><!----></div>"]


def test_content_digest_on_filled_and_empty_elements():
    """Filled strings should get a digest but empty strings should not."""
    html = """
        <div>
            <p>Text</p>
            <p></p>
        </div>
    """.strip()
    soup = BeautifulSoup(html, 'html.parser')
    elements = [str(plain_element(element, True, True)) for element in soup.contents]
    assert elements == ['<div><p data-content-digest="71988c4d8e0803ba4519f0b2864c1331c14a1890bf8694e251379177bfedb5c3">Text</p><p data-content-digest=""></p></div>']


def test_leaf_nodes_without_text():
    """Leaf nodes with text should yield their text, while those without should yield None."""
    html = """
        <div>
            <p>Some text</p>
            <p></p>
            <p>Some more text</p>
        </div>
    """.strip()
    soup = BeautifulSoup(html, 'html.parser')
    text_blocks = [plain_text_leaf_node(paragraph) for paragraph in soup.find_all("p")]
    assert text_blocks == [{'text': 'Some text'}, {'text': None}, {'text': 'Some more text'}]


def test_node_index_assignment():
    """Whitelisted elements should get an appropriate index but bare strings should not."""
    html = """
        <div>
            <p>Some text</p>
            <p></p>
            Some bare text
        </div>
    """.strip()
    soup = BeautifulSoup(html, 'html.parser')
    normalised_strings = [normalise_text(str(add_node_indexes(elem))) for elem in soup.find_all("div")[0].children]
    normalised_strings = [s for s in normalised_strings if s]
    assert normalised_strings == ['<p data-node-index="0">Some text</p>', '<p data-node-index="0"></p>', 'Some bare text']


def test_content_digest_assignment():
    """No content digest hash should be assigned when no child elements exist."""
    html = """
        <div>
            <p>Some text</p>
            <p></p>
            Some bare text
        </div>
    """.strip()
    soup = BeautifulSoup(html, 'html.parser')
    digests = [content_digest(elem) for elem in soup.find_all()]
    assert digests == ['5271913f47bd4cbfda56ff8c0cddfc481d6bc4fe99725906068fbb6144bfeab4',
                       '4c2e9e6da31a64c70623619c449a040968cdbea85945bf384fa30ed2d5d24fa3',
                       '']
