from app import create_app, db

from app.models import User, Article, Highlight, Topic, highlights_topics, Tag, tags_articles, tags_highlights

app=create_app()

def data(): 
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