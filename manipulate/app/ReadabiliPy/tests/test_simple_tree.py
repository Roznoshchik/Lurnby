"""Tests for simple_tree functions."""
from ..readabilipy import simple_tree_from_html_string
from ..readabilipy.simplifiers import strip_html_whitespace


def test_remove_cdata():
    """Test all possible methods of CData inclusion. Note that in the final
    example the '//' prefixes have no effect (since we are not in a <script>)
    tag and so we expect that the first will be displayed (tested in Chrome and
    Safari)."""
    html = """
        <div>
            <p>Some text <![CDATA[Text inside two tags]]></p>
            <![CDATA[Text inside one tag]]>
        </div>
        <![CDATA[Text outside tags]]>
        <script type="text/javascript">
            //<![CDATA[
            document.write("<");
            //]]>
        </script>
        //<![CDATA[
            invalid CDATA block
        //]]>
    """.strip()
    parsed_html = str(simple_tree_from_html_string(html))
    expected_output = "<div><div><p>Some text</p></div><p>//</p></div>"
    assert strip_html_whitespace(parsed_html) == expected_output
