from datetime import date, datetime, timedelta
import os
from random import randint
import sys
import json
from rq import get_current_job
from flask import render_template
from bs4 import BeautifulSoup
import re
import app
from app import create_app, db, s3, bucket, CustomLogger
from app.export import get_zip
from app.email import send_email
from app.main.ebooks import epubTitle, epubConverted
from app.main.pdf import importPDF
from app.models import Task, Article, Highlight, User

logger = CustomLogger("Tasks")

try:
    app.redis.ping()
    app = create_app()
    app.app_context().push()
except Exception:
    pass


def _set_task_progress(progress):
    try:
        app.redis.ping()
        job = get_current_job()
        if job:
            logger.info(f"Job: {job}")
            job.meta["progress"] = progress
            job.save_meta()
            logger.info(f"task id: {job.get_id()}")
            task = Task.query.get(job.get_id())
            logger.info(f"Task: {task}")
            task.user.add_notification(
                "task_progress", {"task_id": job.get_id(), "progress": progress}
            )
            if progress >= 100:
                task.complete = True
            db.session.commit()
    except Exception:
        pass


def delete_user(id):
    u = User.query.filter_by(id=id).first()
    highlights = u.highlights.all()
    topics = u.topics.all()
    articles = u.articles.all()
    tags = u.tags.all()
    senders = u.approved_senders.all()
    comms = u.comms

    for h in highlights:
        db.session.execute(f"DELETE from highlights_topics where highlight_id={h.id}")
        db.session.execute(f"DELETE from tags_highlights where highlight_id={h.id}")
        db.session.delete(h)
    for t in topics:
        db.session.execute(f"DELETE from highlights_topics where topic_id={t.id}")
        db.session.delete(t)
    for t in tags:
        db.session.execute(f"DELETE from tags_articles where tag_id={t.id}")
        db.session.execute(f"DELETE from tags_highlights where tag_id={t.id}")
        db.session.delete(t)
    for a in articles:
        db.session.execute(f"DELETE from tags_articles where article_id={a.id}")
        db.session.delete(a)
    for s in senders:
        db.session.delete(s)
    if comms:
        db.session.delete(comms)

    u.email = None
    u.goog_id = None
    u.firstname = None
    u.username = None
    u.add_by_email = None
    u.token = None
    u.deleted = True
    db.session.commit()


def account_export(uid, ext, delete=False):
    try:
        _set_task_progress(0)
        user = User.query.filter_by(id=uid).first()
        if ext != "none":
            logger.info("exporting")
            if os.environ.get("DEV"):
                az_path_base = f"staging/{user.id}/exports/"
            else:
                az_path_base = f"{user.id}/exports/"
            filename = get_zip(user, ext)
            az_path = f"{az_path_base}lurnby-export.zip"
            s3.upload_file(Bucket=bucket, Filename=filename, Key=az_path)
            url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": az_path},
                ExpiresIn=604800,
            )

            delete_date = (datetime.today() + timedelta(days=7)).strftime("%B %d, %Y")
            logger.info(
                f"sending email - [Lurnby] Your exported data for user: {user.id}"
            )
            send_email(
                "[Lurnby] Your exported data",
                sender=app.config["ADMINS"][0],
                recipients=[user.email],
                text_body=render_template(
                    "email/export_highlights.txt",
                    url=url,
                    user=user,
                    delete_date=delete_date,
                ),
                html_body=render_template(
                    "email/export_highlights.html",
                    url=url,
                    user=user,
                    delete_date=delete_date,
                ),
                sync=True,
            )
        if delete:
            delete_user(user.id)

    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=sys.exc_info())


def export_highlights(user, highlights, source, ext):
    if not highlights:
        return
    try:
        _set_task_progress(0)
        data = []
        i = 0
        total_highlights = len(highlights)

        basedir = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(basedir, "temp")

        if not os.path.isdir(path):
            os.mkdir(path)

        if os.environ.get("DEV"):
            az_path_base = f"staging/{user.id}/exports/"
        else:
            az_path_base = f"{user.id}/exports/"

        if ext == "txt":
            if source == "article":
                a = Article.query.get(highlights[0].article_id)
                title = a.title
                a_source = a.source_url if a.source_url else a.source
                with open(f"{path}/highlights.txt", "w", encoding="utf-16") as f:
                    f.write(f"FROM: {title} \nSOURCE: {a_source}\n\n")
                    for highlight in highlights:
                        highlight = Highlight.query.get(highlight.id)
                        f.write(f"TEXT:\n{highlight.text}\n\n")
                        if highlight.note:
                            f.write(f"NOTE:\n{highlight.note}\n\n")
                        if highlight.topics.count() > 0:
                            topic_titles = [
                                topic.title
                                for topic in highlight.topics.filter_by(
                                    archived=False
                                ).all()
                            ]
                            f.write(f'TOPICS:\n{", ".join(topic_titles)}\n\n')
                        i += 1
                        _set_task_progress(100 * i // total_highlights)
                    f.write("\n")
            else:
                with open(f"{path}/highlights.txt", "w", encoding="utf-16") as f:
                    for highlight in highlights:
                        highlight = Highlight.query.get(highlight.id)
                        a = highlight.article
                        title = a.title
                        a_source = a.source_url if a.source_url else a.source
                        f.write(f"FROM: {title}\nSOURCE: {a_source}\n\n")
                        f.write(f"TEXT:\n{highlight.text}\n\n")
                        if highlight.note:
                            f.write(f"NOTE:\n{highlight.note}\n\n")
                        topic_titles = [
                            topic.title
                            for topic in highlight.topics.filter_by(
                                archived=False
                            ).all()
                        ]
                        f.write(f'TOPICS:\n{", ".join(topic_titles)}\n\n')
                        f.write("\n")

                        i += 1
                        _set_task_progress(100 * i // total_highlights)
                    f.write("\n")

            filename = f"{path}/highlights.txt"
            az_path = f"{az_path_base}highlights.txt"
            s3.upload_file(Bucket=bucket, Filename=filename, Key=az_path)
            url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": az_path},
                ExpiresIn=604800,
            )

            logger.info(
                f"sending email - [Lurnby] Your exported data for user: {user.id}"
            )
            send_email(
                "[Lurnby] Your exported highlights",
                sender=app.config["ADMINS"][0],
                recipients=[user.email],
                text_body=render_template(
                    "email/export_highlights.txt", url=url, user=user
                ),
                html_body=render_template(
                    "email/export_highlights.html", url=url, user=user
                ),
                sync=True,
            )

        else:
            for highlight in highlights:
                highlight = Highlight.query.get(highlight.id)
                if source == "topics":
                    data.append(
                        {
                            "from": highlight.article.title,
                            "source": highlight.article.source_url
                            if highlight.article.source_url
                            else highlight.article.source,
                            "text": highlight.text,
                            "note": highlight.note,
                            "topics": [
                                topic.title
                                for topic in highlight.topics.filter_by(
                                    archived=False
                                ).all()
                            ],
                        }
                    )
                else:
                    data.append(
                        {
                            "text": highlight.text,
                            "note": highlight.note,
                            "topics": [
                                topic.title
                                for topic in highlight.topics.filter_by(
                                    archived=False
                                ).all()
                            ],
                        }
                    )
                i += 1
                _set_task_progress(100 * i // total_highlights)

            with open(f"{path}/highlights.json", "w", encoding="utf-16") as f:
                f.write(json.dumps({"highlights": data}, ensure_ascii=False, indent=4))

            filename = f"{path}/highlights.json"
            az_path = f"{az_path_base}highlights.json"
            s3.upload_file(Bucket=bucket, Filename=filename, Key=az_path)

            url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": az_path},
                ExpiresIn=604800,
            )

            logger.info(
                f"sending email - [Lurnby] Your exported data for user: {user.id}"
            )
            send_email(
                "[Lurnby] Your exported highlights",
                sender=app.config["ADMINS"][0],
                recipients=[user.email],
                text_body=render_template(
                    "email/export_highlights.txt", url=url, user=user
                ),
                html_body=render_template(
                    "email/export_highlights.html", url=url, user=user
                ),
                sync=True,
            )

    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=sys.exc_info())
    finally:
        _set_task_progress(100)


def bg_add_article(article_uuid=None, file_ext=None, file=None):
    try:
        _set_task_progress(0)
        article = Article.query.filter_by(uuid=article_uuid).first()

        today = date.today()
        today = today.strftime("%B %d, %Y")

        if not file:
            basedir = os.path.abspath(os.path.dirname(__file__))
            path = os.path.join(basedir, "temp")

            if not os.path.isdir(path):
                os.mkdir(path)

            path = f"{path}/{article_uuid}"

        if file_ext == ".pdf":
            if not file:
                file = f"{path}.pdf"
                s3.download_file(bucket, article_uuid, file)

            _set_task_progress(10)
            pdf = importPDF(file, article.user)
            _set_task_progress(90)
            source = "PDF File: added " + today
            article.content = pdf["content"]
            article.source = source
            article.title = pdf["title"]
            article.filetype = "pdf"

            article.date_read_date = datetime.utcnow().date()  # why is this needed?
            article.date_read = datetime.utcnow()
            article.estimated_reading()
            article.processing = False

            db.session.commit()
            os.remove(f"{path}.pdf")
            s3.delete_object(Bucket=bucket, Key=article_uuid)

        else:
            if not file:
                file = f"{path}.epub"
                s3.download_file(bucket, article_uuid, file)

            content = epubConverted(file, article.user)
            title = epubTitle(file)
            title = title[0][0]
            epubtext = content

            source = "Epub File: added " + today
            article.title = title
            article.content = epubtext
            article.source = source
            article.filetype = "epub"

            article.date_read_date = datetime.utcnow().date()
            article.date_read = datetime.utcnow()
            article.estimated_reading()
            article.processing = False
            db.session.commit()
            os.remove(f"{path}.epub")
            s3.delete_object(Bucket=bucket, Key=article_uuid)

    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=sys.exc_info())
    finally:
        _set_task_progress(100)
        return


def set_images_lazy(aid):
    try:
        _set_task_progress(0)
        a = Article.query.filter_by(id=aid).first()
        soup = BeautifulSoup(a.content, "html5lib")
        images = soup.find_all("img")
        for img in images:
            img["loading"] = "lazy"
        a.content = str(soup.prettify())
        db.session.commit()
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=sys.exc_info())
    finally:
        _set_task_progress(100)


def set_absolute_urls(aid):
    try:
        _set_task_progress(0)
        a = Article.query.filter_by(id=aid).first()
        if a.source_url:
            soup = BeautifulSoup(a.content, "html5lib")
            images = soup.find_all("img")
            for img in images:
                try:
                    if "http" not in img["src"]:
                        img["src"] = f'{a.source_url}{img["src"]}'
                except Exception:
                    logger.info("no src in image")
            links = soup.find_all("a")
            for link in links:
                try:
                    if "http" not in link["href"]:
                        link["href"] = f'{a.source_url}{link["href"]}'
                except Exception:
                    logger.info("no href in url")
            a.content = str(soup.prettify())
            db.session.commit()

    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=sys.exc_info())
    finally:
        _set_task_progress(100)


# Also consider changing the algorithm for finding the spaces
# to be a bit more sophisticated.
def create_recall_text(highlightId):
    highlight = Highlight.query.filter_by(id=highlightId).first()
    soup = BeautifulSoup(highlight.text, features="lxml")
    for text in soup.find_all(text=True):
        words = text.split(" ")
        if len(words) > 3:
            for i in range(0, len(words) // 3):
                num = randint(0, len(words) - 1)
                words[num] = re.sub(r"[\w\d]+", "_____", words[num])
        text.replace_with(" ".join(words))

    highlight.prompt = soup.prettify()
    db.session.commit()
