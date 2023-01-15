import json
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
        self.client = self.app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_user_fails_without_data(self):
        res = self.client.post('/api/users', json={"a": "b"})
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(data['message'], 'must include username email, and password fields')
    
    def test_create_user(self):
        res = self.client.post('/api/users', json={
            "username": "test@test.com",
            "email": "test@test.com",
            "password": "foo"
            })
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(True, 'id' in data)
        self.assertEqual(True, 'token' in data)

    

if __name__ == "__main__":
    unittest.main(verbosity=2)
