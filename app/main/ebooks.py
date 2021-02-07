import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from bs4.element import Tag


def epubConverted(filepath):
    book = epub.read_epub(filepath)
    chapters = []

    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            chapters.append(item.get_content())
    string = ''

    for item in chapters:
        soup = BeautifulSoup(item, 'lxml')

        for i in soup.contents:
            if isinstance(i, Tag):
                for child in i.children:
                    if child.name == 'body':
                        for tag in child:
                            string += str(tag)

    return string


def epub2html(filepath):
    book = epub.read_epub(filepath)
    chapters = []

    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            chapters.append(item.get_content())

    return chapters


def epubTitle(filepath):
    book = epub.read_epub(filepath)
    title = book.get_metadata('DC', 'title')

    return title


blacklist = ['[document]', 'noscript', 'header', 'html', 'meta',
             'head', 'input', 'script']


def chap2text(chapters):
    output = ''
    soup = BeautifulSoup(chapters, 'html.parser')

    text = soup.find_all(text=True)

    for t in text:
        if t.parent.name not in blacklist:
            output += '{} '.format(t)

    return output


def html2text(html):
    content = []

    for item in html:
        text = chap2text(item)
        content.append(text)

    return content


def epub2text(epub):
    chapters = epub2html(epub)
    content = html2text(chapters)

    return content
