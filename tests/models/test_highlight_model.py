import unittest
from app import create_app, db
from app.models import User, Highlight, Topic
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"


class HighlightModelCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_highlights_topics(self):
        u = User(username="john")
        db.session.add(u)

        h1 = Highlight(text="this is a highlight", user_id=u.id, archived=False)
        h2 = Highlight(text="This is a second highlight", user_id=u.id, archived=False)
        t1 = Topic(title="Canaries", user_id=u.id, archived=False)
        t2 = Topic(title="Bluejays", user_id=u.id, archived=False)

        db.session.add_all([h1, h2, t1, t2])
        db.session.commit()

        self.assertEqual(h1.topics.all(), [])
        self.assertEqual(h2.topics.all(), [])

        h1.AddToTopic(t1)
        db.session.commit()

        self.assertTrue(h1.is_added_topic(t1))
        self.assertEqual(h1.topics.count(), 1)
        self.assertEqual(h1.topics.first().title, "Canaries")
        self.assertEqual(t1.highlights.count(), 1)
        self.assertEqual(t1.highlights.first().text, "this is a highlight")

        h1.RemoveFromTopic(t1)
        db.session.commit()

        self.assertFalse(h1.is_added_topic(t1))
        self.assertEqual(h1.topics.count(), 0)
        self.assertEqual(t1.highlights.count(), 0)

    def test_show_members(self):
        u = User(username="john")
        db.session.add(u)
        u = User.query.first()

        h1 = Highlight(text="this is a highlight", user_id=u.id, archived=False)
        h2 = Highlight(text="This is a second highlight", user_id=u.id, archived=False)
        h3 = Highlight(text="This is a third highlight", user_id=u.id, archived=False)
        h4 = Highlight(text="This is a fourth highlight", user_id=u.id, archived=False)

        t1 = Topic(title="Canaries", user_id=u.id, archived=False)
        t2 = Topic(title="Bluejays", user_id=u.id, archived=False)
        t3 = Topic(title="Crows", user_id=u.id, archived=False)
        t4 = Topic(title="Ravens", user_id=u.id, archived=False)

        db.session.add_all([h1, h2, h3, h4, t1, t2, t3, t4])
        db.session.commit()

        # h1 in 2 lists - Canaries + Crows
        h1.AddToTopic(t1)
        h1.AddToTopic(t3)

        # h2 in 1 list - Bluejays
        h2.AddToTopic(t2)

        # h3 in all lists - Canaries, Bluejays, Crows, Ravens
        h3.AddToTopic(t1)
        h3.AddToTopic(t2)
        h3.AddToTopic(t3)
        h3.AddToTopic(t4)
        # h4 not in any lists

        db.session.commit()

        m1 = h1.topics.all()
        m2 = h2.topics.all()
        m3 = h3.topics.all()
        m4 = h4.topics.all()

        nm1 = h1.not_in_topics(u)
        nm2 = h2.not_in_topics(u)
        nm3 = h3.not_in_topics(u)
        nm4 = h4.not_in_topics(u)

        self.assertCountEqual(m1, [t1, t3])
        self.assertCountEqual(nm1, [t2, t4])

        self.assertCountEqual(m2, [t2])
        self.assertCountEqual(nm2, [t1, t3, t4])

        self.assertCountEqual(m3, [t1, t2, t3, t4])
        self.assertCountEqual(nm3, [])

        self.assertCountEqual(m4, [])
        self.assertCountEqual(nm4, [t1, t2, t3, t4])
