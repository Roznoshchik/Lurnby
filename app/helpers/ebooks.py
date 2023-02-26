import os
from zipfile import ZipFile

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from bs4.element import Tag
from flask_login import current_user
from werkzeug.utils import secure_filename

from app import s3, bucket


def convert_epub(filepath, user=None):
    if not user:
        user = current_user
    book = epub.read_epub(filepath)
    chapters = []

    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            chapters.append(item.get_content())
    html = ""

    for item in chapters:
        soup = BeautifulSoup(item, "lxml")
        soup = process_images(soup, filepath, user)
        soup = process_links(soup)

        for i in soup.contents:
            if isinstance(i, Tag):
                for child in i.children:
                    if child.name == "body":
                        for tag in child:
                            html += str(tag)
    return html


def process_links(soup):
    links = soup.find_all("a", href=True)

    for link in links:
        if "#" in link["href"]:
            x = link["href"].split("#")
            link["href"] = f"#{x[1]}"
        elif "http" not in link["href"]:
            link["href"] = ""
    return soup


def process_images(soup, filepath, user):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    temp_dir = os.path.join(base_dir, "temp")

    if not os.path.isdir(temp_dir):
        os.mkdir(temp_dir)

    title = get_epub_title(filepath)
    title = secure_filename(title)
    epub_dir = os.path.join(temp_dir, title)

    with ZipFile(filepath, "r") as zip:
        zip.extractall(path=epub_dir)

    if os.environ.get("DEV"):
        az_path_base = f"staging/{user.id}/{title}"
    else:
        az_path_base = f"{user.id}/{title}"

    images = soup.find_all("image")
    if images:
        for img in images:
            img["loading"] = "lazy"
            file_name = os.path.basename(img["xlink:href"])
            file_path = find_img_path(epub_dir, file_name)
            az_path = f"{az_path_base}/{file_name}"
            if file_path is not None:
                img["xlink:href"] = upload_to_s3_and_get_url(
                    file_path, az_path, user=user
                )

    images = soup.find_all("img")
    if images:
        for img in images:
            img["loading"] = "lazy"
            file_name = os.path.basename(img["src"])
            file_path = find_img_path(epub_dir, file_name)
            az_path = f"{az_path_base}/{file_name}"
            if file_path is not None:
                img["src"] = upload_to_s3_and_get_url(file_path, az_path, user=user)

    return soup


def find_img_path(base_dir, file_name):
    for dirpath, _, filenames in os.walk(base_dir):
        if file_name in filenames:
            return os.path.join(dirpath, file_name)


def upload_to_s3_and_get_url(file_path, az_path, user):
    if ".svg" in file_path:
        s3.upload_file(
            Bucket=bucket,
            ExtraArgs={"ContentType": "image/svg+xml"},
            Filename=file_path,
            Key=az_path,
        )
    else:
        s3.upload_file(Bucket=bucket, Filename=file_path, Key=az_path)

    return f"/download/{user.id}/{az_path}"


def get_epub_title(filepath):
    book = epub.read_epub(filepath)

    # always returns a list with a tuple [('title', {})]
    title = book.get_metadata("DC", "title")[0][0]

    return title
