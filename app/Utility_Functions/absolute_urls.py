from bs4 import BeautifulSoup
from app import db


def set_absolute_urls(*articles):
    for a in articles:
        if a.source_url:
            soup = BeautifulSoup(a.content, "html5lib")
            images = soup.find_all("img")
            for img in images:
                try:
                    if 'http' not in img['src']:
                        img['src'] = f'{a.source_url}{img["src"]}'
                except:
                    print(f'error with article: {a.uuid}\n img: \n{img}')
            links = soup.find_all('a')
            for l in links:
                try:
                    if 'http' not in l['href']:
                        l['href'] = f'{a.source_url}{l["href"]}'
                except:
                    print(f'error with article: {a.uuid}\n url: \n{l}')

            a.content = str(soup.prettify())
    db.session.commit()