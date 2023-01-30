from bs4 import BeautifulSoup as Soup
import csv
import json
import os
from zipfile import ZipFile

from app import CustomLogger
from app.api.errors import LurnbyValueError
from app.models import Article

logger = CustomLogger("Export Helpers")


def create_zip_file_for_article(article: Article, path: str, ext: str):
    """creates the zip file

    Args:
        article (class Article): Article being exported
        path (str): path to temp dir
        ext (string): 'csv', 'json', or 'txt'
    """
    try:
        ext = ext.lower()
        if ext not in ["csv", "txt", "json"]:
            raise LurnbyValueError('ext must be one of "csv", "txt", or "json"')

        zip_title = "_".join(article.title.split())
        zip_path = os.path.join(path, f"{zip_title}.zip")

        article_dict = create_plain_text_article_dict(article)
        article_highlights = create_list_of_highlight_dicts(article.highlights.all())

        if ext == "csv":
            article_path, highlights_path = export_to_csv(
                path, article_dict, article_highlights
            )

        if ext == "txt":
            article_path, highlights_path = export_to_txt(
                path, article_dict, article_highlights
            )

        if ext == "json":
            article_path, highlights_path = export_to_json(
                path, article_dict, article_highlights
            )

        with ZipFile(zip_path, "w") as myzip:
            myzip.write(article_path, os.path.basename(article_path))
            myzip.write(highlights_path, os.path.basename(highlights_path))

        os.remove(article_path)
        os.remove(highlights_path)
        return zip_path

    except Exception as e:
        logger.error(e)
        raise e


def export_to_json(path, article_dict, article_highlights):
    article_path = f"{path}/article.json"
    highlights_path = f"{path}/highlights.json"

    with open(article_path, "w") as file:
        file.write(json.dumps(article_dict, indent=4))

    with open(highlights_path, "w") as file:
        file.write(json.dumps(article_highlights, indent=4))

    return article_path, highlights_path


def export_to_txt(path, article_dict, article_highlights):
    article_path = f"{path}/article.txt"
    highlights_path = f"{path}/highlights.txt"

    with open(article_path, "w") as file:
        for key, val in article_dict.items():
            if key and val:
                file.write("-" * len(key))
                file.write("\n")
                file.write(key)
                file.write("\n")
                file.write("-" * len(key))
                file.write("\n")
                file.write(val)
                file.write("\n\n")

    with open(highlights_path, "w") as file:
        for highlight in article_highlights:
            had_data = False
            for key, val in highlight.items():
                if key and val:
                    had_data = True
                    file.write("-" * len(key))
                    file.write("\n")
                    file.write(key)
                    file.write("\n")
                    file.write("-" * len(key))
                    file.write("\n")
                    file.write(val)
                    file.write("\n\n")
            if had_data:
                file.write("\n")
                file.write("*" * 40)
                file.write("\n")

    return article_path, highlights_path


def export_to_csv(path, article_dict, article_highlights):
    article_path = f"{path}/article.csv"
    highlights_path = f"{path}/highlights.csv"

    with open(article_path, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, article_dict.keys())
        writer.writeheader()
        writer.writerow(article_dict)

    with open(highlights_path, "w", newline="") as csvfile:
        if len(article_highlights):
            writer = csv.DictWriter(csvfile, article_highlights[0].keys())
            writer.writeheader()
            for highlight in article_highlights:
                writer.writerow(highlight)

    return article_path, highlights_path


def create_plain_text_article_dict(article):
    return {
        "title": article.title,
        "source": article.source_url or article.source,
        "notes": make_plain_text(article.notes),
        "reflections": make_plain_text(article.reflections),
        "tags": ", ".join(article.tag_list),
    }


def create_list_of_highlight_dicts(highlights):
    highlights_list = []
    for highlight in highlights:
        highlights_list.append(
            {
                "text": make_plain_text(highlight.text),
                "note": make_plain_text(highlight.note),
                "prompt": make_plain_text(highlight.prompt),
                "from": highlight.article.title,
                "source": highlight.article.source_url or highlight.article.source,
                "tags": ", ".join([tag.name for tag in highlight.tags.all()]),
                "topics": ", ".join([topic.title for topic in highlight.topics.all()]),
            }
        )
    return highlights_list


def make_plain_text(text):
    if not isinstance(text, str):
        raise LurnbyValueError('Text must be of type "str"')

    return Soup(text, features="html5lib").text
