from bs4 import BeautifulSoup
from app import db
from app.models import Article


def protect_images():
    articles = Article.query.all()
    for a in articles:
        soup = BeautifulSoup(a.content, "html.parser")
        images = soup.find_all("img")
        for img in images:
            try:
                if "/download/" in img["src"]:
                    u = img["src"].replace("/download/", f"/download/{a.user_id}/")
                    img["src"] = u
            except Exception:
                pass
        a.content = str(soup.prettify())
    db.session.commit()
