from app import create_app, db, s3, bucket
import os, json, zipfile



from bs4 import BeautifulSoup as Soup


def get_zip(user, ext):
    basedir = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(
        basedir, f'users/{user.email}'
    )
    if not os.path.isdir(path):
        os.makedirs(path)
    
    path_to_zip = os.path.join(
        basedir, f'users/{user.email}.zip'
    )

    article_export(user, user.articles.filter_by(archived=False).all(), ext)
    topics_export(user, user.topics.filter_by(archived=False).all(), ext)
    highlights_export(user, user.highlights.filter_by(archived=False).all(), ext)

    with zipfile.ZipFile(path_to_zip, mode='w') as zipf:
        len_dir_path = len(path)
        for root, _, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, file_path[len_dir_path:])
    
    return path_to_zip

def article_export(user, articles, ext):
    basedir = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(
        basedir, f'users/{user.email}/articles'
    )
    
    if not os.path.isdir(path):
        os.makedirs(path)

    if ext == 'txt':
        for a in articles:
            title=a.title
            notes=''
            if a.notes:
                notes = Soup(a.notes, features="lxml")
                notes = notes.get_text()
            with open(f'{path}/{title}_notes.txt', 'w') as f:
                f.write(a.title)
                f.write('\n')
                if a.source:
                    f.write(a.source)
                    f.write('\n')
                if a.source_url:
                    f.write(a.source_url)
                    f.write('\n')
                f.write('\n')
                tags = [t.name for t in a.tags.all()]
                f.write(', '.join(tags))
                f.write('\n\n')
                f.write(notes)
            with open(f'{path}/{title}_highlights.txt', 'w') as f:
                f.write(a.title)
                f.write('\n\n')
                for h in a.highlights.all():
                    f.write(f'FROM: {h.article.title} \n')
                    if h.article.source:
                        f.write(f'Source: {h.article.source} \n')
                    if h.article.source_url:
                        f.write(f'URL: {h.article.source_url} \n')
                    f.write('\n')
                    f.write(h.text)
                    f.write('\n')
                    if h.note:
                        f.write('HIGHLIGHT NOTE ')
                        f.write('\n')
                        f.write(h.note)
                        f.write('\n')
                    if h.topics.count() > 0:
                        f.write('HIGHLIGHT TOPICS ')
                        f.write('\n')
                        topics = [t.title for t in h.topics.all()]
                        f.write(', '.join(topics))
                        f.write('\n\n')
                    else:
                        f.write('\n')       

    
    else:
        for a in articles:
            data = {}
            data['Title'] = a.title
            data['Source']= a.source_url if a.source_url else a.source
            data['Notes'] =  a.notes
            data['Tags']= [t.name for t in a.tags.filter_by(archived=False).all()]
            a_highlights = a.highlights.filter_by(archived=False).all()
            highlights = []
            for h in a_highlights:
                highlight={}
                highlight['text'] = h.text
                highlight['note'] = h.note
                highlight['topics'] = [t.title for t in h.topics.filter_by(archived=False).all()]
                highlights.append(highlight)
            data['Highlights'] = highlights

            with open(f'{path}/{a.title}_notes.json', 'w', encoding='utf-16') as f:
                f.write(json.dumps(data, ensure_ascii=False, indent=4))


def topics_export(user, topics, ext):
    basedir = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(
        basedir, f'users/{user.email}/topics'
    )

    if not os.path.isdir(path):
        os.makedirs(path)
    

    if ext == 'txt':
        for t in topics:
            highlights = t.highlights.filter_by(archived=False).all()
            with open(f'{path}/{t.title}.txt', 'w') as f:
                f.write(f'{t.title} \n\n')
                for h in highlights:
                    f.write(f'FROM: {h.article.title} \n\n')
                    if h.article.source:
                        f.write(f'Source: {h.article.source}\n\n')
                    if h.article.source_url:
                        f.write(f'URL: {h.article.source_url} \n\n')
                    f.write(f'TOPICS\n')
                    f.write(f'{", ".join([t.title for t in h.topics.filter_by(archived=False).all()])}\n\n')
                    f.write(f'TEXT\n{h.text}\n\n')
                    f.write(f'Note\n{h.note}\n\n\n\n')

    else:
        for t in topics:
            data = {}
            data['Title'] = t.title
            highlights = []
            for h in t.highlights.filter_by(archived=False).all():
                highlight={}
                highlight['From'] = h.article.title
                highlight['Source'] = h.article.source_url if h.article.source_url else h.article.source
                highlight['Topics'] = [t.title for t in h.topics.filter_by(archived=False).all()]
                highlight['Text'] = h.text
                highlight['Note'] = h.note
                highlights.append(highlight)
            data['Highlights'] = highlights

            with open(f'{path}/{t.title}.json', 'w', encoding='utf-16') as f:
                    f.write(json.dumps(data, ensure_ascii=False, indent=4))
    


def highlights_export(user, highlights, ext):
    basedir = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(
        basedir, f'users/{user.email}/highlights'
    )

    if not os.path.isdir(path):
        os.makedirs(path)
    

    if ext == 'txt':
        with open(f'{path}/highlights.txt', 'w') as f:
            f.write(f'HIGHLIGHTS \n\n')
            for h in highlights:
                f.write(f'FROM: {h.article.title} \n\n')
                if h.article.source:
                    f.write(f'Source: {h.article.source}\n\n')
                if h.article.source_url:
                    f.write(f'URL: {h.article.source_url} \n\n')
                f.write(f'TOPICS\n')
                f.write(f'{", ".join([t.title for t in h.topics.filter_by(archived=False).all()])}\n\n')
                f.write(f'TEXT\n{h.text}\n\n')
                f.write(f'Note\n{h.note}\n\n\n\n')

    else:
            data = {}
            l_highlights = []
            for h in highlights:
                highlight={}
                highlight['From'] = h.article.title
                highlight['Source'] = h.article.source_url if h.article.source_url else h.article.source
                highlight['Topics'] = [t.title for t in h.topics.filter_by(archived=False).all()]
                highlight['Text'] = h.text
                highlight['Note'] = h.note

                l_highlights.append(highlight)
            data['Highlights'] = l_highlights

            with open(f'{path}/highlights.json', 'w', encoding='utf-16') as f:
                    f.write(json.dumps(data, ensure_ascii=False, indent=4))
    
