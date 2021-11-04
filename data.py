import datetime
from sqlalchemy import desc

from app import create_app
from app.models import User, Event

app = create_app()


def print_data():
    count = User.query.count()
    users = User.query.all()
    print("Total Users: " + str(count))
    print('\n')

    for u in users:
        print(u.email)
        print("articles " + str(u.articles.count()))
        print("highlights " + str(u.highlights.count()))
        print("topics " + str(u.topics.count()))
        print("tags " + str(u.tags.count()))
        print('\n')


def data_dashboard():
    users = User.query.filter_by(test_account=False).order_by(desc(User.last_active)).limit(15)
    user_list = []
    for u in users:
        ev = u.events.order_by(Event.date.desc()).limit(1).first()
        try: 
            last_active = ev.date
        except:
            last_active = u.last_active

        try:
            last_action = ev.name
        except:
            last_action = u.last_action



        user = {
            'id': u.id,
            'email': u.email,
            'articles': u.articles.count(),
            'highlights': u.highlights.count(),
            'topics': u.topics.count(),
            'tags': u.tags.count(),
            'last_active': last_active,
            'test_account': u.test_account,
            'last_action': last_action,
        }
        try:
            user['suggestion'] = u.suggestion.title
        except:
            user['suggestion'] = None


        user_list.append(user)

    return user_list
