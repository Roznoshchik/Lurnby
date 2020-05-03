import pytest
from ..readabilipy.extractors.extract_title import extract_title
from ..readabilipy.extractors.extract_title import combine_similar_titles


htmls_with_expected = [
    ("""<meta name="fb_title" content="Example title 1" />""", "Example title 1"),
    ("""<meta property="og:title" content="Example title 2" />""", "Example title 2"),
    ("""<head><title>Example title 3</title></head>""", "Example title 3"),
    ("""<head><title><p>Example title 4</p></title></head>""", "Example title 4"),
    ("""<meta itemprop="headline" content="Example title 5" />)""", "Example title 5"),
    ("""<meta name="sailthru.title" content="Example title 6" />)""", "Example title 6"),
    ("""<meta name="dcterms.title" content="Example title 7" />)""", "Example title 7"),
    ("""<meta name="title" content="Example title 8" />)""", "Example title 8"),
    ("""<header name="entry-header"><h1 class="entry-title">Example title 9</h1></header>""", "Example title 9"),
    ("""<h1 class="entry-title">Example title 10</h1>""", "Example title 10"),
    ("""<header><h1>Example title 11</h1></header>""", "Example title 11"),
    ("""<h1 class="title">Example title 12</h1>""", "Example title 12"),
    ("""<h1 itemprop="headline">Example title 13</h2>""", "Example title 13"),
    ("""<h2 itemprop="headline">Example title 14</h2>""", "Example title 14"),
    ("""<h2 class="title">Example title 15</h2>""", None),  # not one of the xpaths in extract_title()
    ("""<div class="postarea"><h2><a>Example title 16</a></h2></div>""", "Example title 16"),
    ("""<body><title>Example title 17</title></body>""", "Example title 17"),
]


@pytest.mark.parametrize("html, expected", htmls_with_expected)
def test_extract_title(html, expected):
    assert extract_title(html) == expected


def test_extract_title_prioritises_highest_score_xpath():

    html = """
            <h2 class="title">Silly title</h2>
            <h1 class="entry-title">Example title</h1>
            <header><h1>Bad title</h1></header>
            <p>Hello world</p>
    """
    expected = "Example title"
    assert extract_title(html) == expected


def test_extract_title_removes_unwanted_characters():

    html = """
        <meta property="og:title" content="Trump Denies Charitable Donation He Promised If Elizabeth Warren Releases DNA Results And It&#8217;s On Video" />
    """
    expected = "Trump Denies Charitable Donation He Promised If Elizabeth Warren Releases DNA Results And It’s On Video"
    assert extract_title(html) == expected


def test_extract_title_gets_text_within_hyperlinks():

    html = """
        <h1 class="entry-title">
            <a href="http://addictinginfo.com/2018/10/15/trump-denies-charitable-donation-he-promised-if-elizabeth-warren-releases-dna-results-and-its-on-video/"
                title="Permalink to Trump Denies Charitable Donation He Promised If Elizabeth Warren Releases DNA Results And It&#8217;s On Video"
                rel="bookmark">Trump Denies Charitable Donation He Promised If Elizabeth Warren Releases DNA Results And
                It&#8217;s On Video</a>
        </h1>
    """
    expected = "Trump Denies Charitable Donation He Promised If Elizabeth Warren Releases DNA Results And It’s On Video"
    assert extract_title(html) == expected


def test_extract_title_pick_shortest_version_of_equivalent_title():

    html = """
            <h1 class="entry-title">Pamela Geller in Breitbart News: Dueling Billboards from CAIR, AFDI in Times Square</h1>
            <meta property="og:title" content="Pamela Geller in Breitbart News: Dueling Billboards from CAIR, AFDI in Times Square - Geller Report" />
        """
    expected = "Pamela Geller in Breitbart News: Dueling Billboards from CAIR, AFDI in Times Square"
    assert extract_title(html) == expected


def test_combine_similar_titles():

    extracted_strings = {}
    extracted_strings['title 1'] = {'score': 1, 'xpaths': ['a']}
    extracted_strings['Title 1'] = {'score': 1, 'xpaths': ['b']}
    extracted_strings['Title 1 - Extended'] = {'score': 1, 'xpaths': ['c']}

    expected_output = {}
    expected_output['title 1'] = {'score': 1, 'xpaths': ['a']}
    expected_output['Title 1'] = {'score': 3, 'xpaths': ['a', 'b', 'c']}
    expected_output['Title 1 - Extended'] = {'score': 1, 'xpaths': ['c']}

    assert combine_similar_titles(extracted_strings) == expected_output
