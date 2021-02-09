import json
import os
from ..readabilipy import simple_json_from_html_string
from ..readabilipy.simplifiers import strip_html_whitespace
from ..readabilipy.simple_json import extract_text_blocks_as_plain_text


def get_normalised_html_output(test_fragment, expected_output=None):
    """Get normalised HTML output."""
    if expected_output is None:
        expected_output = test_fragment
    article_json = simple_json_from_html_string(test_fragment)
    content = str(article_json["plain_content"])
    # Check that expected output is present after simplifying the HTML
    normalised_expectation = strip_html_whitespace(expected_output)
    normalised_result = strip_html_whitespace(content)
    print("expectation:", normalised_expectation)
    print("result:", normalised_result)
    return (normalised_expectation, normalised_result)


def check_exact_html_output(test_fragment, expected_output=None):
    """Check that expected output is present when parsing HTML fragment."""
    normalised_expectation, normalised_result = \
        get_normalised_html_output(test_fragment, expected_output)
    assert normalised_expectation == normalised_result


def check_html_output_contains_text(test_fragment, expected_output=None):
    """Check that expected output is present when parsing HTML fragment."""
    normalised_expectation, normalised_result = \
        get_normalised_html_output(test_fragment, expected_output)
    assert normalised_expectation in normalised_result


def check_extract_article(test_filename, expected_filename,
                          content_digests=False, node_indexes=False,
                          use_readability_js=False):
    """Test end-to-end article extraction. Ensure that HTML from
       file matches JSON from file after parsing is applied."""
    test_data_dir = "data"
    # Read HTML test file
    test_filepath = os.path.join(os.path.dirname(__file__),
                                 test_data_dir, test_filename)
    with open(test_filepath) as h:
        html = h.read()

    # Extract simplified article HTML
    if use_readability_js:
        article_json = simple_json_from_html_string(html, content_digests,
                                                    node_indexes,
                                                    use_readability=True)
    else:
        article_json = simple_json_from_html_string(html, content_digests,
                                                    node_indexes)

    # Get expected simplified article HTML
    expected_filepath = os.path.join(os.path.dirname(__file__),
                                     test_data_dir, expected_filename)
    with open(expected_filepath) as h:
        expected_article_json = json.loads(h.read())

    # Test full JSON matches (checks for unexpected fields in either actual
    # or expected JSON)
    assert article_json == expected_article_json


def check_extract_paragraphs_as_plain_text(test_filename, expected_filename):
    test_data_dir = "data"
    # Read readable article test file
    test_filepath = os.path.join(os.path.dirname(__file__), test_data_dir,
                                 test_filename)
    with open(test_filepath) as h:
        article = json.loads(h.read())

    # Extract plain text paragraphs
    paragraphs = extract_text_blocks_as_plain_text(article["plain_content"])

    # Get expected plain text paragraphs
    expected_filepath = os.path.join(os.path.dirname(__file__),
                                     test_data_dir, expected_filename)
    with open(expected_filepath) as h:
        expected_paragraphs = json.loads(h.read())

    # Test
    assert paragraphs == expected_paragraphs


def check_html_has_no_output(test_fragment):
    """Check that no output is present when parsing HTML fragment."""
    article_json = simple_json_from_html_string(test_fragment)
    # Check that there is no output
    assert article_json["plain_content"] is None or \
        article_json["plain_content"] == "<div></div>"


def check_html_output_does_not_contain_tag(test_fragment, vetoed_tag):
    """Check that vetoed tag is not present when parsing HTML fragment."""
    article_json = simple_json_from_html_string(test_fragment)
    # Check that neither <tag> nor </tag> appear in the output
    content = str(article_json["plain_content"])
    if content is not None:
        for element in ["<{}>".format(vetoed_tag),
                        "</{}>".format(vetoed_tag)]:
            assert element not in content
