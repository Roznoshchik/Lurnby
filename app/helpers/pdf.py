from io import BytesIO
import os

import fitz
from flask_login import current_user
from werkzeug.utils import secure_filename

from app import s3, bucket

IMAGE = 1


def importPDF(file, user=None):

    filepath = file.filename if hasattr(file, "filename") else file
    doc = fitz.open(filepath)
    title, title_for_dir = get_titles(doc)

    processed = {}
    content = ""

    url_dict = process_images_and_get_url_dict(doc, title_for_dir, user)
    sizes = create_sizes_to_header_tags_dict(doc)

    for page in doc:
        page_contents = page.get_text("dict")["blocks"]
        for item in page_contents:
            if item["type"] == IMAGE:
                content += url_dict.get(item["number"], "")
            else:
                lines = item.get("lines", {})

                for line in lines:
                    spans = line["spans"]
                    for span in spans:
                        tag = sizes.get(span["size"], "p")
                        content += f"<{tag}>{span['text']}</{tag}>"

    processed["content"] = content
    processed["title"] = title

    return processed


def process_images_and_get_url_dict(pdf_doc, title_for_dir, user):
    if not user:
        user = current_user

    az_path_base = get_path(title_for_dir, user)
    img_count = 0

    url_dict = {}

    for page in pdf_doc:
        page_contents = page.get_text("dict")["blocks"]
        for item in page_contents:
            if item["type"] == 1:
                ext = item["ext"]
                file_name = f"{img_count}.{ext}"
                img_count += 1

                # Create a BytesIO buffer and write the image data to it
                buffer = BytesIO()
                buffer.write(item["image"])

                # Upload the data from the buffer to S3
                az_path = az_path_base + file_name
                s3.put_object(Bucket=bucket, Key=az_path, Body=buffer.getvalue())

                url = f"/download/{user.id}/{az_path}"
                url_dict[item["number"]] = f'<img src ={url} loading="lazy">'

    return url_dict


def create_sizes_to_header_tags_dict(pdf_doc):
    # get all font sizes in doc
    sizes = {}
    for page in pdf_doc:
        page_contents = page.get_text("dict")["blocks"]
        for item in page_contents:
            if item["type"] == 0:
                lines = item["lines"]
                for line in lines:
                    spans = line["spans"]
                    for span in spans:
                        sizes[span["size"]] = span["size"]
        for size in sizes:
            if size > 40:
                sizes[size] = "h1"
            elif size < 40 and size > 30:
                sizes[size] = "h2"
            elif size < 30 and size > 25:
                sizes[size] = "h3"
            elif size < 25 and size > 20:
                sizes[size] = "h4"
            elif size < 20 and size > 16:
                sizes[size] = "h5"
            else:
                sizes[size] = "p"

    return sizes


def get_titles(pdf_doc):
    title = pdf_doc.metadata.get("title", "")
    if title == "":
        title = pdf_doc.load_page(0).get_text()[:155] + "..."

    title_for_dir = secure_filename(title)

    return title, title_for_dir


def get_path(title_for_dir, user):

    if os.environ.get("DEV"):
        az_path_base = f"staging/{user.id}/{title_for_dir}/"
    else:
        az_path_base = f"{user.id}/{title_for_dir}/"

    return az_path_base
