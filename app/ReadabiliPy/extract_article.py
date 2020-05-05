import argparse
import json
from .readabilipy import simple_json_from_html_string


def main():
    parser = argparse.ArgumentParser(
        description="Extract article data from a HTML file using either Mozilla's Readability.js package or a simplified python-only alternative.")
    parser.add_argument('-i', '--input-file', required=True,
                        help="Path to input file containing HTML.")
    parser.add_argument('-o', '--output-file', required=True,
                        help="Path to file to output the article data to as JSON.")
    parser.add_argument('-c', '--content-digests', action='store_true',
                        help="Add a 'data-content-digest' attribute containing a SHA256-based digest of the element's contents to each HTML element in the plain_content output.")
    parser.add_argument('-n', '--node-indexes', action='store_true',
                        help="Add a 'data-node-index' attribute containing a hierarchical representation of the element's position in the HTML structure each HTML element in the plain_content output.")
    parser.add_argument('-p', '--use-python-parser', action='store_true',
                        help="Use the pure-python 'plain_html' parser included in this project rather than Mozilla's Readability.js.")

    args = parser.parse_args()

    with open(args.input_file) as h:
        html = h.read()

    article = simple_json_from_html_string(html, content_digests=args.content_digests,
                                           node_indexes=args.node_indexes, use_readability=(not args.use_python_parser))

    with open(args.output_file, "w") as j:
        json.dump(article, j, ensure_ascii=False)


if __name__ == '__main__':
    main()
