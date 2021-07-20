import random
import sys
from faker import Faker
from app import db
from app.models import Article


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
                          article_created_date = faker.date_time(),
                          user_id = u
                          )
        
        db.session.add(article)      
        article.estimated_reading()

        if not article.unread:
            article.progress = faker.pyfloat(min_value=0.0, max_value=100.0)
            article.done= faker.boolean(chance_of_getting_true=25)

        
        
    db.session.commit()
    print(f'Added {n} fake articles to the database.')