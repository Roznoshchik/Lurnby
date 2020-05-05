import os
from ..readabilipy import simple_json_from_html_string
from ..readabilipy.extractors import extract_date, extract_title


TEST_FILEPATH = os.path.join(os.path.dirname(__file__), "data", "benchmarkinghuge.html")
with open(TEST_FILEPATH) as h:
    HTML = h.read()


def test_benchmark_simple_json_from_html_string(benchmark):
    benchmark(simple_json_from_html_string, html=HTML)


def test_benchmark_extract_title(benchmark):
    benchmark(extract_title, html=HTML)


def test_benchmark_extract_date(benchmark):
    benchmark(extract_date, html=HTML)
