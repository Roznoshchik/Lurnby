from collections import defaultdict
from ..readabilipy.extractors.extract_element import extract_element


def test_extract_element():
    xpaths = [
        ('//h1[@class="entry-title"]//text()', 4),
        ('//h1[@itemprop="headline"]//text()', 3),
    ]

    html = """
            <h1 class="entry-title">Title 1</h>
            <p></p>
            <h1 itemprop="headline">Title 2</h>
            <p></p>
            <h1 class="post__title">Title 2</h>
    """

    expected_output_1 = defaultdict(dict)
    expected_output_1['Title 1'] = \
        {'score': 4, 'xpaths': ['//h1[@class="entry-title"]//text()']}
    expected_output_1['Title 2'] = \
        {'score': 3, 'xpaths': ['//h1[@itemprop="headline"]//text()']}

    assert extract_element(html, xpaths) == expected_output_1


def test_extract_element_with_passed_func():
    def process_dict(d):
        d['Title 1'] = 7
        return d

    xpaths = [
        ('//h1[@class="entry-title"]//text()', 4),
        ('//h1[@itemprop="headline"]//text()', 3),
    ]

    html = """
            <h1 class="entry-title">Title 1</h>
            <p></p>
            <h1 itemprop="headline">Title 2</h>
            <p></p>
            <h1 class="post__title">Title 2</h>
    """

    expected_output_3 = defaultdict(dict)
    expected_output_3['Title 1'] = 7
    expected_output_3['Title 2'] = \
        {'score': 3, 'xpaths': ['//h1[@itemprop="headline"]//text()']}

    assert extract_element(html, xpaths, process_dict_fn=process_dict) \
        == expected_output_3
