from .checks import check_extract_article


def test_extract_simple_article_with_readability_js():
    check_extract_article(
        "plain-content-test_full_article.html",
        "plain-content-test_full_article_javascript.json",
        use_readability_js=True
    )


def test_extract_article_from_page_with_readability_js():
    check_extract_article(
        "addictinginfo.com-1_full_page.html",
        "addictinginfo.com-1_full_page_javascript.json",
        use_readability_js=True
    )
