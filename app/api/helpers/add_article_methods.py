from flask import jsonify, url_for
from pathlib import Path
import validators

from app import db, CustomLogger, s3, bucket
from app.api.exceptions import LurnbyValueError
from app.main.pulltext import pull_text
from app.models import Tag

logger = CustomLogger("API")


def process_manual_entry(article, manual_entry):
    """process manually supplied entry

    Args:
        article (class 'app.models.Article'): Instantiated article
        manual_entry (dict): {title:str, content: str, source: str }

    Returns:
        article (class 'app.models.Article'): Updated with manual entry data
    """

    title = manual_entry.get("title")
    content = manual_entry.get("content")
    source = manual_entry.get("source")

    if not title or not content:
        raise LurnbyValueError("Missing Title or Content")

    article.content = content
    article.title = title
    article.source = source
    article.filetype = "manual"

    return article


def process_url_entry(article, url):
    """gets content from a url

    Args:
        article (class 'app.models.Article'): Instantiated article
        url (str): url to some content

    Returns:
        article (class 'app.models.Article'): Updated with url content
    """

    if not validators.url(url):
        raise LurnbyValueError(
            "Can't validate url. Please check the data and try again"
        )

    try:
        processed_url = pull_text(url)
        title = processed_url.get("title")
        content = processed_url.get("content")

        if not title or not content:
            raise Exception

    except Exception:
        logger.error(f"Couldn't parse url: {url}")
        raise LurnbyValueError("Something went wrong. Please check the url")

    article.title = title
    article.content = content
    article.source_url = url

    return article


def add_to_tags(article, user_id, tags=[]):
    """creates tags if they don't exist and adds them to the article

    Args:
        article (class 'app.models.Article'): Instantiated article
        user_id (int): id for the current user
        tags (list): list of tag names. Defaults to [].

    Returns:
        article (class 'app.models.Article'): Updated with tags
    """

    for tag_name in tags:
        tag = Tag.query.filter_by(name=tag_name).first()
        if not tag:
            tag = Tag(user_id=user_id, name=tag_name)
            db.session.add(tag)

        article.AddToTag(tag)

    return article


def process_file(article=None, file=None, user=None):
    """Launches a task for processing the supplied file
    and returns the task id to the client

    Args:
        article (class 'app.models.Article'): Instantiated article
        file (.epub or .pdf): _description_. Defaults to None.
        user (class 'app.models.User'): User from token_auth.current_user()

    Returns:
        response object: status_code = 201, json={task_id:str, article_id: int, processing:bool}
    """
    if not article or not file or not user:
        raise LurnbyValueError("Bad request")

    file_ext = Path(file.filename).suffix
    if file_ext != ".epub" and file_ext != ".pdf":
        db.session.delete(article)
        db.session.commit()
        raise LurnbyValueError("File must be pdf or epub")
    else:
        task = user.launch_task(
            "bg_add_article",
            article_uuid=str(article.uuid),
            file_ext=file_ext,
            file=file,
        )
        response = jsonify(processing=True, task_id=task.id, article=article.to_dict())
        response.status_code = 201
        return response


def process_file_upload(article, upload_file_ext):
    """generates a presigned url for uploading a file to s3
    returns the presigned url to the client for uploading and
    also returns the url to ping when the upload is complete

    Args:
        article (class 'app.models.Article'): instantiated article
        upload_file_ext (str): .epub or .pdf

    Returns:
        response object: status_code = 201,
        json={
          upload_url:str,
          location: str,
          upload_file_ext:str,
          article_id: int,
          processing:bool
          }
    """
    if upload_file_ext and "." not in upload_file_ext:
        upload_file_ext = f".{upload_file_ext}"

    if not upload_file_ext or (
        upload_file_ext != ".epub" and upload_file_ext != ".pdf"
    ):
        raise LurnbyValueError('upload_file_ext should be ".epub" or ".pdf"')

    upload_url = s3.generate_presigned_url(
        ClientMethod="put_object",
        Params={"Bucket": bucket, "Key": str(article.uuid)},
        ExpiresIn=3600,
    )

    response = jsonify(
        processing=True,
        upload_url=upload_url,
        article=article.to_dict(),
        upload_file_ext=upload_file_ext,
        location=url_for("api.file_uploaded", article_uuid=str(article.uuid)),
    )

    response.status_code = 201
    return response
