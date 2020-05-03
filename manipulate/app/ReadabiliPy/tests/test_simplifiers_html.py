"""Tests for plain_html functions."""
from bs4 import BeautifulSoup
from ..readabilipy.simplifiers import html


def test_remove_metadata():
    HTML = """
        <!DOCTYPE html>
        <html>
        <head></head>
        <body>
        <!-- Comment here -->
        </body>
        </html>
    """
    soup = BeautifulSoup(HTML, "html5lib")
    html.remove_metadata(soup)
    assert "<!-- Comment here -->" not in str(soup)


def test_remove_blacklist():
    HTML = """
        <html>
        <body>
            <button type="button">Click Me!</button>
            <p>Hello</p>
        <body>
        </html>
    """
    soup = BeautifulSoup(HTML, "html5lib")
    html.remove_blacklist(soup)
    assert "button" not in str(soup)
