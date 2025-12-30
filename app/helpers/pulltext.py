# from readabilipy import simple_json_from_html_string
# import requests

# this uses a readability port to clean up the text
# This version of readabilipy is updated with a later version of mozilla code
# it returns the cleaned up html or text.

import requests
from app.ReadabiliPy.readabilipy.simple_json import simple_json_from_html_string


def pull_text(url):

    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=30)
    response.encoding = "utf-8"
    article = simple_json_from_html_string(
        response.text, content_digests=False, node_indexes=False, use_readability=True
    )
    return article
