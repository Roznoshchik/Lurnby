# this uses a readability port to clean up the text
# it returns the cleaned up html or text.

def pull_text(url):
    import sys
    sys.path.insert(1, './app/ReadabiliPy')
    from readabilipy import simple_json_from_html_string

    import requests

    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)

    article = simple_json_from_html_string(response.text,
                                           content_digests=False,
                                           node_indexes=False,
                                           use_readability=True)

    return article
