import os
from zipfile import ZipFile

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from bs4.element import Tag
from flask_login import current_user
from werkzeug.utils import secure_filename

from app import s3, bucket


def epubConverted(filepath, u=None):
    if not u:
        u = current_user
    book = epub.read_epub(filepath)
    chapters = []

    basedir = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(basedir, "temp")

    if not os.path.isdir(path):
        os.mkdir(path)

    title = epubTitle(filepath)
    title = secure_filename(title)
    path = os.path.join(basedir, "temp", title)
    if os.environ.get("DEV"):
        az_path_base = f"staging/{u.id}/{title}/"
    else:
        az_path_base = f"{u.id}/{title}/"

    with ZipFile(filepath, "r") as zip:
        zip.extractall(path=path)

    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            chapters.append(item.get_content())
    string = ""

    for item in chapters:
        soup = BeautifulSoup(item, "lxml")

        images = soup.find_all("image")
        if images:
            for img in images:
                img["loading"] = "lazy"
                filename = img["xlink:href"]
                filename = filename.replace("../", path + "/")
                if not os.path.exists(filename):
                    filename = img["xlink:href"]
                    filename = filename.replace("../", path + "/OEBPS/")
                # print(filename)

                if not os.path.exists(filename):
                    filename = img["xlink:href"]
                    filename = filename.replace("../", path + "/OPS/")
                # print(filename)

                if not os.path.exists(filename):
                    filename = img["xlink:href"]
                    filename = filename.replace("../", path + "/EPUB/media/")
                # print(filename)

                if not os.path.exists(filename):
                    filename = img["xlink:href"]
                    filename = filename.replace("../", path + "/EPUB/images/")
                # print(filename)

                if not os.path.exists(filename):
                    filename = img["xlink:href"]
                    filename = filename.replace("../", path + "/EPUB/")
                # print(filename)
                if not os.path.exists(filename):
                    filename = f'{path}/{img["xlink:href"]}'
                # print(filename)

                if not os.path.exists(filename):
                    filename = f'{path}/OEBPS/{img["xlink:href"]}'
                # print(filename)

                if not os.path.exists(filename):
                    filename = f'{path}/oebps/{img["xlink:href"]}'
                # print(filename)

                if not os.path.exists(filename):
                    filename = f'{path}/OPS/{img["xlink:href"]}'
                # print(filename)

                if not os.path.exists(filename):
                    filename = f'{path}/ops/{img["xlink:href"]}'
                # print(filename)

                if not os.path.exists(filename):
                    continue
                    print("still can't find image folder")

                name = os.path.basename(filename)
                az_path = az_path_base + name
                if ".svg" in name:
                    s3.upload_file(
                        Bucket=bucket,
                        ExtraArgs={"ContentType": "image/svg+xml"},
                        Filename=filename,
                        Key=az_path,
                    )
                else:
                    s3.upload_file(Bucket=bucket, Filename=filename, Key=az_path)
                # location = s3.get_bucket_location(Bucket=bucket)['LocationConstraint']
                # url = "https://s3-%s.amazonaws.com/%s/%s" % (location, bucket, az_path)
                url = f"/download/{u.id}/{az_path}"
                img["xlink:href"] = url

        images = soup.find_all("img")
        if images:
            for img in images:
                img["loading"] = "lazy"
                filename = img["src"]
                filename = filename.replace("../", path + "/")
                # print(f'path: {path}')
                if not os.path.exists(filename):
                    filename = f"{path}/{img['src']}"
                # print(f'filename: {filename}')
                ## print(filename)

                if not os.path.exists(filename):
                    filename = f"{path}/EPUB/media/{img['src']}"
                # print(f'filename: {filename}')
                # print(filename)

                if not os.path.exists(filename):
                    filename = f"{path}/EPUB/images/{img['src']}"
                    # print(f'filename: {filename}')
                    # print(filename)

                if not os.path.exists(filename):
                    filename = f"{path}/EPUB/{img['src']}"
                    # print(f'filename: {filename}')
                    # print(filename)

                if not os.path.exists(filename):
                    filename = img["src"]
                    filename = filename.replace("../", path + "/OEBPS/")
                # print(f'filename: {filename}')
                ## print(filename)

                if not os.path.exists(filename):
                    filename = img["src"]
                    filename = filename.replace("../", path + "/oebps/")
                # print(f'filename: {filename}')
                ## print(filename)

                if not os.path.exists(filename):
                    filename = img["src"]
                    filename = filename.replace("../", path + "/OPS/")
                # print(f'filename: {filename}')
                ## print(filename)

                if not os.path.exists(filename):
                    filename = img["src"]
                    filename = filename.replace("../", path + "/ops/")
                # print(f'filename: {filename}')
                ## print(filename)

                if not os.path.exists(filename):
                    filename = f"{path}/OEBPS/{img['src']}"
                # print(f'filename: {filename}')

                if not os.path.exists(filename):
                    filename = f"{path}/oebps/{img['src']}"
                # print(f'filename: {filename}')

                if not os.path.exists(filename):
                    filename = f"{path}/OPS/{img['src']}"
                # print(f'filename: {filename}')

                if not os.path.exists(filename):
                    filename = f"{path}/ops/{img['src']}"
                # print(f'filename: {filename}')

                if not os.path.exists(filename):
                    print("still cant find img folder")
                    continue

                name = os.path.basename(filename)
                az_path = az_path_base + name
                if ".svg" in name:
                    s3.upload_file(
                        Bucket=bucket,
                        ExtraArgs={"ContentType": "image/svg+xml"},
                        Filename=filename,
                        Key=az_path,
                    )
                else:
                    s3.upload_file(Bucket=bucket, Filename=filename, Key=az_path)

                location = s3.get_bucket_location(Bucket=bucket)["LocationConstraint"]
                url = "https://s3-%s.amazonaws.com/%s/%s" % (location, bucket, az_path)
                url = f"/download/{u.id}/{az_path}"

                img["src"] = url

        links = soup.find_all("a", href=True)
        for link in links:
            ## print(l['href'])
            if "#" in link["href"]:
                x = link["href"].split("#")
                ## print(x)
                link["href"] = f"#{x[1]}"
                ## print(l['href'])
            elif "http" not in link["href"]:
                link["href"] = ""

        for i in soup.contents:
            if isinstance(i, Tag):
                for child in i.children:
                    if child.name == "body":
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

    # always returns a list with a tuple [('title', {})]
    title = book.get_metadata("DC", "title")[0][0]

    return title


blacklist = [
    "[document]",
    "noscript",
    "header",
    "html",
    "meta",
    "head",
    "input",
    "script",
]


def chap2text(chapters, path, az_path):
    output = ""
    soup = BeautifulSoup(chapters, "html.parser")

    images = soup.find_all("img")
    if images:
        for img in images:
            img["src"] = img["src"].replace("../", path + "/")
            filename = img["src"]
            if not os.path.exists(filename):
                filename = filename.replace(path, path + "/OEBPS")
            if not os.path.exists(filename):
                continue

            name = os.path.basename(filename)
            az_path = az_path + name

            s3.upload_file(Bucket=bucket, Filename=filename, Key=az_path)
            location = s3.get_bucket_location(Bucket=bucket)["LocationConstraint"]
            url = "https://s3-%s.amazonaws.com/%s/%s" % (location, bucket, az_path)
            img["src"] = url

    # text = soup.find_all(text=True)

    for t in soup:
        if t.parent.name not in blacklist:
            output += "{} ".format(t)

    return output


def html2text(html):
    content = []
    epub = html[0]

    basedir = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(basedir, "temp")

    if not os.path.isdir(path):
        os.mkdir(path)

    title = epubTitle(epub)
    title = secure_filename(title)
    path = os.path.join(basedir, "temp", title)

    with ZipFile(epub, "r") as zip:
        zip.extractall(path=path)

    for item in html[1]:
        text = chap2text(item)
        content.append(text)

    return content


def epub2text(epub):
    html = epub2html(epub)
    content = html2text(html)

    return content
