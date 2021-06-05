from bs4 import BeautifulSoup
from app import db
from app.models import Article

def protect_images():
    articles = Article.query.all()
    for a in articles:
        soup = BeautifulSoup(a.content, "html.parser")
        images = soup.find_all('img')
        for img in images:
            try:
                if "https://s3-us-east-2.amazonaws.com/lurnby/" in img['src']:
                    u = img['src'].replace('https://s3-us-east-2.amazonaws.com/lurnby/', '/download/')
                    img['src'] = u
            except:
                pass
        a.content = str(soup.prettify())
    db.session.commit()