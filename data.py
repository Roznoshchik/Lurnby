import json

from app import create_app, db
from app.models import User, Article, Highlight, Topic, highlights_topics, Tag, tags_articles, tags_highlights

app=create_app()

def print_data(): 
    count = User.query.count()
    users = User.query.all()
    print("Total Users: "+str(count))
    print('\n')
    
    for u in users:
        print(u.email)
        print("articles "+ str(u.articles.count()))
        print("highlights "+ str(u.highlights.count()))
        print("topics "+ str(u.topics.count()))
        print("tags "+str(u.tags.count()))
        print('\n')

def data_dashboard():
    users = User.query.all()
    user_list=[]
    for u in users:
        user = {
            'id':u.id,
            'email':u.email,
            'articles':u.articles.count(),
            'highlights':u.highlights.count(),
            'topics': u.topics.count(),
            'tags': u.tags.count(),
            'test_account': u.test_account
        }

        user_list.append(user)

    return user_list




