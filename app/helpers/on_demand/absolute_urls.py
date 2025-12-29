from bs4 import BeautifulSoup
from app import db, CustomLogger

logger = CustomLogger("Helpers")


def set_absolute_urls(*articles):
    for a in articles:
        if a.source_url:
            soup = BeautifulSoup(a.content, "html5lib")
            images = soup.find_all("img")
            for img in images:
                try:
                    if "http" not in img["src"]:
                        img["src"] = f'{a.source_url}{img["src"]}'
                except Exception:
                    logger.error(f"set_absolute_urls - error with article: {a.uuid}\n img: \n{img}")
            links = soup.find_all("a")
            for link in links:
                try:
                    if "http" not in link["href"]:
                        link["href"] = f'{a.source_url}{link["href"]}'
                except Exception:
                    logger.error(f"set_absolute_urls error with article: {a.uuid}\n url: \n{link}")

            a.content = str(soup.prettify())
    db.session.commit()


def fix_article_note_links(a):
    if a.notes and a.notes != "":
        soup = BeautifulSoup(a.notes, "html5lib")
        links = soup.find_all("a")
        for link in links:
            try:
                if "/article/" not in link["href"]:
                    link["href"] = f'/article/{link["href"]}'
            except Exception:
                logger.error(f"fix_article_note_links -  error with article: {a.uuid}\n url: \n{link}")
        a.notes = str(soup.prettify())
    db.session.commit()
