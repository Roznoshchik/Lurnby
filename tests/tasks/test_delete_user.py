import unittest
from app import db, create_app
from app.models import User, Highlight, Approved_Sender, Tag, Article, Comms
from app.tasks import delete_user
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"


class DeleteUser(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_delete_user(self):
        # create a user and some associated data
        u = User(
            goog_id='123',
            firstname='John',
            username='jdoe',
            email='jdoe@example.com',
            password_hash='foo'
        )
        h1 = Highlight(text='highlight1', user=u)
        h2 = Highlight(text='highlight2', user=u)
        a1 = Article(title='article1', user=u)
        a2 = Article(title='article2', user=u)
        t1 = Tag(name='tag1', user=u)
        t2 = Tag(name='tag2', user=u)
        s1 = Approved_Sender(email='sender1', user=u)
        s2 = Approved_Sender(email='sender2', user=u)
        comms = Comms(user=u)
        db.session.add_all([u, h1, h2, a1, a2, t1, t2, s1, s2, comms])
        db.session.commit()

        # call delete_user and make assertions
        delete_user(u.id)
        self.assertTrue(u.deleted)
        self.assertIsNone(u.email)
        self.assertIsNone(u.goog_id)
        self.assertIsNone(u.firstname)
        self.assertIsNone(u.username)
        self.assertIsNone(u.add_by_email)
        self.assertIsNone(u.token)
        self.assertIsNone(u.comms)

        self.assertEqual(Highlight.query.count(), 0)
        self.assertEqual(Article.query.count(), 0)
        self.assertEqual(Tag.query.count(), 0)
        self.assertEqual(Approved_Sender.query.count(), 0)

        self.assertEqual(Highlight.query.filter_by(user_id=u.id).count(), 0)
        self.assertEqual(Article.query.filter_by(user_id=u.id).count(), 0)
        self.assertEqual(Tag.query.filter_by(user_id=u.id).count(), 0)
        self.assertEqual(Approved_Sender.query.filter_by(user_id=u.id).count(), 0)

        self.assertIsNone(Comms.query.filter_by(user_id=u.id).first())
