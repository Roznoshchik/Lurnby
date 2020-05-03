"""Test readability.py on sample articles"""
from .checks import check_extract_article, check_extract_paragraphs_as_plain_text


# Test end-to-end article extraction
def test_extract_article_full_page():
    check_extract_article(
        "addictinginfo.com-1_full_page.html",
        "addictinginfo.com-1_simple_article_from_full_page.json"
    )


def test_extract_article_full_article():
    check_extract_article(
        "addictinginfo.com-1_full_article.html",
        "addictinginfo.com-1_simple_article_from_full_article.json"
    )


def test_extract_article_non_article():
    check_extract_article(
        "non_article_full_page.html",
        "non_article_full_page.json"
    )


def test_extract_article_unicode_normalisation():
    check_extract_article(
        "conservativehq.com-1_full_page.html",
        "conservativehq.com-1_simple_article_from_full_page.json"
    )


def test_extract_article_list_items():
    check_extract_article(
        "list_items_full_page.html",
        "list_items_simple_article_from_full_page.json"
    )


def test_extract_article_headers_and_non_paragraph_blockquote_text():
    check_extract_article(
        "davidwolfe.com-1_full_page.html",
        "davidwolfe.com-1_simple_article_from_full_page.json"
    )


def test_extract_article_list_items_content_digests():
    check_extract_article(
        "list_items_full_page.html",
        "list_items_simple_article_from_full_page_content_digests.json",
        content_digests=True
    )


def test_extract_article_list_items_node_indexes():
    check_extract_article(
        "list_items_full_page.html",
        "list_items_simple_article_from_full_page_node_indexes.json",
        node_indexes=True
    )


def test_extract_article_full_page_content_digest():
    check_extract_article(
        "addictinginfo.com-1_full_page.html",
        "addictinginfo.com-1_simple_article_from_full_page_content_digest.json",
        content_digests=True
    )


def test_extract_article_full_page_node_indexes():
    check_extract_article(
        "addictinginfo.com-1_full_page.html",
        "addictinginfo.com-1_simple_article_from_full_page_node_indexes.json",
        node_indexes=True
    )


def test_extract_article_full_page_content_digest_node_indexes():
    check_extract_article(
        "addictinginfo.com-1_full_page.html",
        "addictinginfo.com-1_simple_article_from_full_page_content_digest_node_indexes.json",
        content_digests=True,
        node_indexes=True
    )


# Test plain text extraction
def test_extract_paragraphs_as_plain_text():
    check_extract_paragraphs_as_plain_text(
        "addictinginfo.com-1_simple_article_from_full_article.json",
        "addictinginfo.com-1_plain_text_paragraphs_from_simple_article.json"
    )


def test_extract_paragraphs_as_plain_text_node_indexes():
    check_extract_paragraphs_as_plain_text(
        "list_items_simple_article_from_full_page_node_indexes.json",
        "list_items_plain_text_paragraph_node_indexes.json"
    )
