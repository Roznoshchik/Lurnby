ReadabiliPy
[![Build Status](https://travis-ci.org/alan-turing-institute/ReadabiliPy.svg?branch=master)](https://travis-ci.org/alan-turing-institute/ReadabiliPy)
[![Coverage Status](https://coveralls.io/repos/github/alan-turing-institute/ReadabiliPy/badge.svg?branch=master)](https://coveralls.io/github/alan-turing-institute/ReadabiliPy?branch=master)
===========
A Node and filesystem dependent Python wrapper for Mozilla's [Readability.js](https://github.com/mozilla/readability) Node.js package.

This package also augments the output of `Readability.js` to also return a list of plain text representations of article paragraphs.

## Package contents
- `javascript` folder
  - `Readability.js`: Taken unaltered from commit [876c81f](https://github.com/mozilla/readability/tree/876c81f710711ba2afb36dd83889d4c5b4fc2743) of Mozilla's [Readability.js](https://github.com/mozilla/readability) Node.js package.

  - `ExtractArticle.js`: A Node.js script that reads a file containing a HTML snippet (does not have to be a full document), parses it using [jsdom](https://github.com/jsdom/jsdom), attempts to extract an article using `Readability.parse()` and writes the output to a JSON file.
    - Usage: `node ExtractArticle.js -i <input_file> -o <output_file>`
    - Arguments:
      - `-i`: The path to an input file containing full or partial HTML as text.
      - `-o`: The path to the file the output article JSON data should be written to.

- `readabilipy` folder
  - `simple_json.py` file containing the function `simple_json_from_html_string()`.
    - Usage:
    ```python
    from readabilipy import simple_json_from_html_string

    article = simple_json_from_html_string(html_string, content_digests=False, node_indexes=False, use_readability=False)
    ```
    - The function returns a dictionary with the following fields:
      - `title`: The article title
      - `byline`: Author information
      - `content`: A simplified HTML representation of the article, with all article text contained in paragraph elements.
      - `plain_content`: A "plain" version of the simplified `Readability.js` article HTML present in the `content` field. This attempts to retain only the plain text content of the article, while preserving the HTML structure.
      - `plain_text`: A list containing plain text representations of each paragraph (`<p>`) or list (`<ol>` or `<ul>`) present in the simplified `Readability.js` article HTML in the `content` field. Each paragraph or list is represented as a single string. List strings look like `"* item 1, * item 2, * item 3,"` for both ordered and unordered lists (note the trailing `,`).
    - All fields are guaranteed to be present. If individual fields are missing from the output of `Readability.js`, the value of these fields will be `None`. If no article data is returned by `Readability.js`, the value of all fields will be `None`.
    - All text in the `plain_content` and `plain_text` fields is encoded as unicode normalised using the "NFKC" normal form. This normal form is used to try and ensure as much as possible that things that appear visually the same are encoded with the same unicode representation (the K part) and characters are represented as a single composite character where possible (the C part).
      - An optional `content_digests` flag can be passed to the Python wrapper. When this is set to `True`, each HTML element in the `plain_content` field has a `data-content-digest` attribute, which holds the SHA-256 hash of its plain text content. For "leaf" nodes (containing only plain text in the output), this is the SHA-256 hash of their plain text content. For nodes containing other nodes, this is the SHA-256 hash of the concatenated SHA-256 hashes of their child nodes.
      - An optional `node_indexes` flag can be passed to the Python wrapper. When this is set to `True`, each HTML element in the `plain_content` field has a `data-node-indexes` attribute, which holds a hierarchical index describing the location of element within the `plain_content` HTML structure.
      - An optional `use_readability` flag can be passed to the Python wrapper. When this is set to `True`, Mozilla's `Readability.js` will be used as the parser. If it is set to `False` then the pure-python parser in `plain_html.py` will be used instead.

  - `simple_tree.py` file containing the function `simple_tree_from_html_string()`.
    - Usage:
    ```python
    from readabilipy import simple_tree_from_html_string

    article = simple_tree_from_html_string(html_string)
    ```
    - The function returns a `bs4.BeautifulSoup` object containing a cleaned, parsed HTML tree.


- `extract_article.py`: A Python script that uses `readabilipy.simple_json_from_html_string()` to extract the augmented readable article data.
  - Usage: `python extract_article.py -i <input_file> -o <output_file> [-c] [-n] [-p]`
  - All arguments have long and short form versions.
    - `-i` / `--input-file`: The path to an input file containing full or partial HTML as text.
    - `-o` / `--output-file`: The path to the file the output article JSON data should be written to.
    - `-c` / `--content-digests` (optional): If this flag is provided, then `simple_json_from_html_string()` is called with `content_digests=True`
    - `-n` / `--node-indexes` (optional): If this flag is provided, then `simple_json_from_html_string()` is called with `node_indexes=True`
    - `-p` / `--use-python-parser` (optional): If this flag is provided then `simple_json_from_html_string()` is called with `use_readability=False`


## Installation
1. [Install Node.js](https://nodejs.org/en/download/)
2. Install the node part of this package by running `npm install`.
3. Install the requirements for the Python part of this package by running:
  - As a user of this project `pip install -r requirements.txt`
  - As a developer of this project `pip install -r requirements-dev.txt`

## Testing
1. Run the tests with `python -m pytest -vv`
