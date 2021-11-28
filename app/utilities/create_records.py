import random
import sys
from faker import Faker
from app import db
from app.models import Article, Topic, Highlight




def create_fake_highlights(n, u):
    """ Generate fake highlights"""
    faker = Faker()
    count = Article.query.count()
    articles = Article.query.all()

    # create topics
    for i in range(25):
        title = faker.text(max_nb_chars=20)
        t = Topic(user_id=u.id, title=title, archived=False)
        db.session.add(t)
    db.session.commit()
    topics = Topic.query.filter_by(user_id = u.id).all()


    for i in range(n):
        content = ""
        notes = ""
        for i in range(random.randrange(4)):
            content += faker.paragraph(nb_sentences=3, variable_nb_sentences=True, ext_word_list=None)
    
        for i in range(random.randrange(5)):
            notes += faker.paragraph(nb_sentences=3, variable_nb_sentences=True, ext_word_list=None)

        i = random.randrange(count)



        h = Highlight(user_id=u.id, 
                      text=content,
                      note=notes,
                      archived=False,
                      no_topics = faker.boolean(chance_of_getting_true=25),
                      article_id=articles[i].id,
                      created_date = faker.date_time()
                      )
        db.session.add(h)
        if not h.no_topics:
            for i in range(random.randrange(10)):
                x = random.randrange(25)
                h.AddToTopic(topics[x])
        
        db.session.commit()




def create_fake_articles(n, u):
    """Generate fake articles."""
    faker = Faker()
    for i in range(n):
        s = ""
        for i in range(random.randrange(543)):
            s += f'<p>{faker.paragraph(nb_sentences=3, variable_nb_sentences=True, ext_word_list=None)}</p>'

        article = Article(title=faker.sentence(nb_words=9, variable_nb_words=True, ext_word_list=None),
                          unread=faker.boolean(chance_of_getting_true=25),
                          content = s,
                          archived=False,
                          date_read = faker.date_time(),
                          date_read_date= faker.date_time().date(),
                          article_created_date = faker.date_time(),
                          user_id = u.id
                          )
        
        db.session.add(article)      
        article.estimated_reading()

        if not article.unread:
            article.progress = faker.pyfloat(min_value=0.0, max_value=100.0)
            article.done= faker.boolean(chance_of_getting_true=25)

        
        
    db.session.commit()
    print(f'Added {n} fake articles to the database.')