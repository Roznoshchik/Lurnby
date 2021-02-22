import os
from zipfile import ZipFile

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from bs4.element import Tag
from werkzeug.utils import secure_filename

from flask_login import current_user

from app import s3, bucket

def get_images(filepath):
    book = epub.read_epub(filepath)
    images = book.get_items_of_type(ebooklib.ITEM_IMAGE)

    return images


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

    html = [filepath, chapters]
    return html


def epubTitle(filepath):
    book = epub.read_epub(filepath)
    title = book.get_metadata('DC', 'title')

    return title


blacklist = ['[document]', 'noscript', 'header', 'html', 'meta',
             'head', 'input', 'script']


def chap2img(chapters, path, az_path):
    output = ''
    soup = BeautifulSoup(chapters, 'html.parser')

    images = soup.find_all('img')
    if images:
        for img in images:
            
            img['src'] = img['src'].replace("../", path+"/")
            filename = img['src']
            if not os.path.exists(filename):
                filename = filename.replace(path, path+'/OEBPS')
            if not os.path.exists(filename):
                continue

            name = os.path.basename(filename)
            az_path = az_path + name

            s3.upload_file(
                    Bucket = bucket,
                    Filename=filename,
                    Key=az_path
                    )
            location = s3.get_bucket_location(Bucket=bucket)['LocationConstraint']
            url = "https://s3-%s.amazonaws.com/%s/%s" % (location, bucket, az_path)
            img['src'] = url
            
    return images


def html2text(html):
    images = []
    epub = html[0]

    basedir = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(
        basedir, 'temp'
    )

    if not os.path.isdir(path):
        os.mkdir(path)

    title = epubTitle(epub)
    title = secure_filename(title[0][0])
    path = os.path.join(
        basedir, 'temp', title
    )

    az_path = f'{current_user.id}/{title}/'
    with ZipFile(epub, 'r') as zip: 
        zip.extractall(path=path)
    
    for item in html[1]:
        
        img = chap2img(item, path, az_path)
        images.append(img)

    return images


def epub2text(epub):
    chapters = epub2html(epub)
    content = html2text(chapters)

    return content
