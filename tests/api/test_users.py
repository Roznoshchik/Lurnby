import unittest
from app import create_app, db
from app.models import User, Highlight, Tag, Topic, Article
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'


class UserApiTests(unittest.TestCase):

    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_user(self):
      print(self.app.test_client)
      self.assertEqual(3,4)

    

if __name__ == "__main__":
    unittest.main(verbosity=2)
