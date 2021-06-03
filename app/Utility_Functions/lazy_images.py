from app import db
from bs4 import BeautifulSoup

def set_images_lazy(*articles):
    for a in articles:
        soup = BeautifulSoup(a.content, "html5lib")
        images = soup.find_all("img")
        for img in images:
            img["loading"] = "lazy"
        a.content = str(soup.prettify())
    db.session.commit()
    