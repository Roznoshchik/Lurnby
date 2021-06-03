from bs4 import BeautifulSoup
from app import db


def set_absolute_urls(*articles):
    for a in articles:
        if a.source_url:
            soup = BeautifulSoup(a.content, "html5lib")
            images = soup.find_all("img")
            for img in images:
                if 'http' not in img['src']:
                    img['src'] = f'{a.source_url}{img["src"]}'
            links = soup.find_all('a')
            for l in links:
                if 'http' not in l['href']:
                    l['href'] = f'{a.source_url}{l["href"]}'
            a.content = str(soup.prettify())
    db.session.commit()