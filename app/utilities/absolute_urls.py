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
                    print(f'set_absolute_urls - error with article: {a.uuid}\n img: \n{img}')
            links = soup.find_all('a')
            for l in links:
                try:
                    if 'http' not in l['href']:
                        l['href'] = f'{a.source_url}{l["href"]}'
                except:
                    print(f'set_absolute_urls error with article: {a.uuid}\n url: \n{l}')

            a.content = str(soup.prettify())
    db.session.commit()



def fix_article_note_links(a):
    if a.notes and a.notes != '':
        soup = BeautifulSoup(a.notes, "html5lib")
        links = soup.find_all('a')
        for l in links:
            try:
                if '/article/' not in l['href']:
                    l['href'] = f'/article/{l["href"]}'
            except:
                print(f'fix_article_note_links -  error with article: {a.uuid}\n url: \n{l}')
        a.notes = str(soup.prettify())
    db.session.commit()