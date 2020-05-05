"""Test readability.py on sample articles"""
from .checks import check_exact_html_output, check_html_output_contains_text


# Test bare text behaviours
def test_html_bare_text():
    """Bare text should be wrapped in <p> tags."""
    check_html_output_contains_text(
        "Bare text here",
        "<p>Bare text here</p>"
    )


def test_html_bare_text_linebreaks():
    """Line breaks in bare text should be removed."""
    check_html_output_contains_text("""
        Bare text with
        some linebreaks here
    """, "<p>Bare text with some linebreaks here</p>")


def test_html_text_with_semantic_br():
    """Single <br> is sometimes used as a word separator so should be replaced
    with a space."""
    check_exact_html_output(
        """<a href="http://example.com">link</a><br />caption""",
        "<div><p>link caption</p></div>"
    )


def test_html_bare_text_double_br():
    """Double <br> in bare text should trigger a new paragraph."""
    check_html_output_contains_text("""
        Bare text with
        <br/><br/>
        some linebreaks here
    """, "<p>Bare text with</p><p>some linebreaks here</p>")


def test_html_space_separated_double_br():
    """Double <br> separated by whitespace should still trigger a new paragraph."""
    check_html_output_contains_text("""
        Bare text with
        <br/>
               <br/>
        some linebreaks here
    """, "<p>Bare text with</p><p>some linebreaks here</p>")


def test_html_space_separated_double_br_inside_div():
    """Double <br> separated by whitespace should still trigger a new div."""
    check_html_output_contains_text("""
        <div>
            Text with
            <br/>
                <br/>
            some linebreaks here
        <div>
    """, "<div><p>Text with</p><p>some linebreaks here</p></div>")


def test_html_space_separated_double_br_inside_and_outside_div():
    """First double <br> should trigger a new <p>, second several <p> inside the div, third a new <p>"""
    check_exact_html_output("""
        <div>
            <p>Some <br/>
            <br/>example text here.</p>
        </div>
        <div>
        Text in a div. <br/>
        <br/> A new div.
        </div>
        Bare text. <br/>
        <br/> A new paragraph.
        """, "<div><div><p>Some</p><p>example text here.</p></div><div><p>Text in a div.</p><p>A new div.</p></div><p>Bare text.</p><p>A new paragraph.</p></div>")


# Test correct wrapping
def test_ensure_correct_outer_div_wrapping():
    """Do not wrap in a <div> if this is already a <div>."""
    check_exact_html_output("""
        <div>
            <p>
                Some example text here.
            </p>
        </div>""", """<div><p>Some example text here.</p></div>""")


def test_ensure_correct_paragraph_wrapping():
    """Do not wrap bare text inside <div> with <p> tags."""
    check_exact_html_output("""
        <div>
            Some example text here.
        </div>""", """<div>Some example text here.</div>""")


# Test consecutive links
def test_consecutive_links():
    """Check that whitespace is preserved between consecutive <a> links."""
    check_exact_html_output("""
        <blockquote>
            <p>First paragraph: <a href="https://example.com">first link</a> <a href="https://example.com">second link</a></p>
            <p>Second paragraph: <a href="https://example.com">third link</a></p>
        </blockquote>""", "<div><blockquote><p>First paragraph: first link second link</p><p>Second paragraph: third link</p></blockquote></div>")


def test_consecutive_links_with_spaces():
    """Check that extra whitespace is remove inside <a> links even when they are consecutive."""
    check_exact_html_output("""
        <blockquote>
            <p>First paragraph: <a href="https://example.com">first link </a> <a href="https://example.com"> second link</a></p>
            <p>Second paragraph: <a href="https://example.com">third link </a></p>
            <p>Third paragraph: <a href="https://example.com">first link </a><a href="https://example.com">second link</a></p>
        </blockquote>""", "<div><blockquote><p>First paragraph: first link second link</p><p>Second paragraph: third link</p><p>Third paragraph: first link second link</p></blockquote></div>")


# Test text consolidation
def test_span_removal_and_conversion():
    """First <span> should be removed. Second should give bare text that will be wrapped."""
    check_exact_html_output("""
        <div>
            <p>Some <span>example</span> text here.</p>
            <span>More text in a span.</span>
        </div>""", "<div><p>Some example text here.</p><p>More text in a span.</p></div>")


def test_consolidating_string_between_tags():
    """First <span> should be removed. Second should give bare text that will be wrapped."""
    check_exact_html_output("""
        <div>
            <p>Some <br><br>example text here.</p>
            <span>More text in a span.</span>
            Part of the same paragraph. <br>
            <br> A new paragraph.
        </div>""", "<div><p>Some</p><p>example text here.</p><p>More text in a span. Part of the same paragraph.</p><p>A new paragraph.</p></div>")


def test_empty_element_removal():
    """Empty elements should be removed."""
    check_exact_html_output("""
        <div>
            <p>Text</p>
            <p></p>
            <span>Paragraphs</span>
        </div>
        Bare <span></span> t<a></a>ext
        <div></div>
    """, "<div><div><p>Text</p><p>Paragraphs</p></div><p>Bare text</p></div>")


def test_single_br_with_semantic_space():
    """Empty elements should be removed."""
    check_exact_html_output("""
        <div>
            <p>This tag<br> will be removed but the space after it is important.</p>
        </div>
    """, "<div><p>This tag will be removed but the space after it is important.</p></div>")


def test_prune_div_with_one_populated_one_empty_span():
    check_exact_html_output("""
        <div>
            <span>dfs</span>
            <span></span>
        </div>
    """, "<div>dfs</div>")


def test_prune_div_with_one_empty_span():
    check_exact_html_output("""
        <div>
            <span></span>
        </div>""", "<div></div>")


def test_prune_div_with_one_whitespace_paragraph():
    check_exact_html_output(
        """<div>
            <p>        </p>
        </div>
        """,
        "<div></div>"
    )
