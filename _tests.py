import unittest
from app import create_app, db
from app.models import User, Highlight, Tag, Topic, Article
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

        self.assertEqual(m1, [t1, t3])
        self.assertEqual(nm1, [t2, t4])

        self.assertEqual(m2, [t2])
        self.assertEqual(nm2, [t1, t3, t4])

        self.assertEqual(m3, [t1, t2, t3, t4])
        self.assertEqual(nm3, [])

        self.assertEqual(m4, [])
        self.assertEqual(nm4, [t1, t2, t3, t4])


class TagModelCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_add_removing_tags(self):
        u = User(username="john")
        db.session.add(u)

        h1 = Highlight(text="this is a highlight", user_id=u.id, archived=False)
        h2 = Highlight(text="This is a second highlight", user_id=u.id, archived=False)
        t1 = Topic(title="Canaries", user_id=u.id, archived=False)
        t2 = Topic(title="Bluejays", user_id=u.id, archived=False)
        a1 = Article(title="Breaking Breaking!", user_id=u.id, archived=False)
        a2 = Article(title="Read all about it!", user_id=u.id, archived=False)
        tag1 = Tag(name="tag1", user_id=u.id, archived=False)
        tag2 = Tag(name="tag2", user_id=u.id, archived=False)

        db.session.add_all([h1, h2, t1, t2, a1, a2, tag1, tag2])
        db.session.commit()

        self.assertEqual(a1.tags.all(), [])
        self.assertEqual(a2.tags.all(), [])

        self.assertEqual(h1.tags.all(), [])
        self.assertEqual(h2.tags.all(), [])

        self.assertEqual(t1.tags.all(), [])
        self.assertEqual(t2.tags.all(), [])

        a1.AddToTag(tag1)

        h1.AddToTag(tag1)

        t1.AddToTag(tag1)
        db.session.commit()

        self.assertTrue(a1.is_added_tag(tag1))
        self.assertEqual(a1.tags.count(), 1)
        self.assertEqual(a1.tags.first().name, "tag1")
        self.assertEqual(tag1.articles.count(), 1)
        self.assertEqual(tag1.articles.first().title, "Breaking Breaking!")

        self.assertTrue(h1.is_added_tag(tag1))
        self.assertEqual(h1.tags.count(), 1)
        self.assertEqual(h1.tags.first().name, "tag1")
        self.assertEqual(tag1.highlights.count(), 1)
        self.assertEqual(tag1.highlights.first().text, "this is a highlight")

        self.assertTrue(t1.is_added_tag(tag1))
        self.assertEqual(t1.tags.count(), 1)
        self.assertEqual(t1.tags.first().name, "tag1")
        self.assertEqual(tag1.topics.count(), 1)
        self.assertEqual(tag1.topics.first().title, "Canaries")

        a1.RemoveFromTag(tag1)
        h1.RemoveFromTag(tag1)
        t1.RemoveFromTag(tag1)
        db.session.commit()

        self.assertFalse(a1.is_added_tag(tag1))
        self.assertEqual(a1.tags.count(), 0)
        self.assertEqual(a1.tags.count(), 0)

    def test_show_members(self):
        u = User(username="john")
        db.session.add(u)
        u = User.query.first()

        h1 = Highlight(text="this is a highlight", user_id=u.id, archived=False)
        h2 = Highlight(text="This is a second highlight", user_id=u.id, archived=False)
        h3 = Highlight(text="this is a third highlight", user_id=u.id, archived=False)
        h4 = Highlight(text="This is a fourth highlight", user_id=u.id, archived=False)

        t1 = Topic(title="Canaries", user_id=u.id, archived=False)
        t2 = Topic(title="Bluejays", user_id=u.id, archived=False)
        t3 = Topic(title="Ravens", user_id=u.id, archived=False)
        t4 = Topic(title="Crows", user_id=u.id, archived=False)

        a1 = Article(title="Breaking Breaking!", user_id=u.id, archived=False)
        a2 = Article(title="Read all about it!", user_id=u.id, archived=False)
        a3 = Article(title="You won't believe!", user_id=u.id, archived=False)
        a4 = Article(title="Top 10 Must See!", user_id=u.id, archived=False)

        tag1 = Tag(name="Lauma", user_id=u.id, archived=False)
        tag2 = Tag(name="Slavs", user_id=u.id, archived=False)
        tag3 = Tag(name="Major", user_id=u.id, archived=False)
        tag4 = Tag(name="Pablo", user_id=u.id, archived=False)

        db.session.add_all(
            [h1, h2, h3, h4, t1, t2, t3, t4, a1, a2, a3, a4, tag1, tag2, tag3, tag4]
        )
        db.session.commit()

        # in 2 tags
        a1.AddToTag(tag1)
        a1.AddToTag(tag3)

        h1.AddToTag(tag1)
        h1.AddToTag(tag3)

        t1.AddToTag(tag1)
        t1.AddToTag(tag3)

        # in 1 tag
        a2.AddToTag(tag2)

        h2.AddToTag(tag2)

        t2.AddToTag(tag2)

        # in all tags
        a3.AddToTag(tag1)
        a3.AddToTag(tag2)
        a3.AddToTag(tag3)
        a3.AddToTag(tag4)

        h3.AddToTag(tag1)
        h3.AddToTag(tag2)
        h3.AddToTag(tag3)
        h3.AddToTag(tag4)

        t3.AddToTag(tag1)
        t3.AddToTag(tag2)
        t3.AddToTag(tag3)
        t3.AddToTag(tag4)

        # a4, h4, t4 not in any tags

        db.session.commit()

        ma1 = a1.tags.all()
        ma2 = a2.tags.all()
        ma3 = a3.tags.all()
        ma4 = a4.tags.all()

        mh1 = h1.tags.all()
        mh2 = h2.tags.all()
        mh3 = h3.tags.all()
        mh4 = h4.tags.all()

        mt1 = t1.tags.all()
        mt2 = t2.tags.all()
        mt3 = t3.tags.all()
        mt4 = t4.tags.all()

        nma1 = a1.not_in_tags(u)
        nma2 = a2.not_in_tags(u)
        nma3 = a3.not_in_tags(u)
        nma4 = a4.not_in_tags(u)

        nmh1 = h1.not_in_tags(u)
        nmh2 = h2.not_in_tags(u)
        nmh3 = h3.not_in_tags(u)
        nmh4 = h4.not_in_tags(u)

        nmt1 = t1.not_in_tags(u)
        nmt2 = t2.not_in_tags(u)
        nmt3 = t3.not_in_tags(u)
        nmt4 = t4.not_in_tags(u)

        self.assertEqual(ma1, [tag1, tag3])
        self.assertEqual(nma1, [tag2, tag4])
        self.assertEqual(ma2, [tag2])
        self.assertEqual(nma2, [tag1, tag3, tag4])
        self.assertEqual(ma3, [tag1, tag2, tag3, tag4])
        self.assertEqual(nma3, [])
        self.assertEqual(ma4, [])
        self.assertEqual(nma4, [tag1, tag2, tag3, tag4])

        self.assertEqual(mh1, [tag1, tag3])
        self.assertEqual(nmh1, [tag2, tag4])
        self.assertEqual(mh2, [tag2])
        self.assertEqual(nmh2, [tag1, tag3, tag4])
        self.assertEqual(mh3, [tag1, tag2, tag3, tag4])
        self.assertEqual(nmh3, [])
        self.assertEqual(mh4, [])
        self.assertEqual(nmh4, [tag1, tag2, tag3, tag4])

        self.assertEqual(mt1, [tag1, tag3])
        self.assertEqual(nmt1, [tag2, tag4])
        self.assertEqual(mt2, [tag2])
        self.assertEqual(nmt2, [tag1, tag3, tag4])
        self.assertEqual(mt3, [tag1, tag2, tag3, tag4])
        self.assertEqual(nmt3, [])
        self.assertEqual(mt4, [])
        self.assertEqual(nmt4, [tag1, tag2, tag3, tag4])


if __name__ == "__main__":
    unittest.main(verbosity=2)
