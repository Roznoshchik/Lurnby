import json
import os
import unittest
from unittest.mock import patch
from app import create_app, db
from app.models import User, Comms
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'


class UserApiTests(unittest.TestCase):

    def setUp(self):
        os.environ['testing'] = '1'
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
            "password": "foo"})
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(True, 'id' in data)
        self.assertEqual(True, 'token' in data)

    @patch('app.models.User.check_token')
    def test_get_user(self, mock_check_token):
        user = User(email='test@test.com')
        db.session.add(user)
        db.session.commit()
        mock_check_token.return_value = User.query.first()
        res = self.client.get('/api/users/1', headers={'Authorization': 'Bearer abc123'})
        data = json.loads(res.data)
        self.assertEqual(data, user.to_dict())

    @patch('app.models.User.check_token')
    def test_update_user(self, mock_check_token):
        user = User(email='test@test.com')
        db.session.add(user)
        db.session.commit()
        mock_check_token.return_value = User.query.first()
        res = self.client.patch('/api/users/1',
                                json={"email": 'foo@bar.com'},
                                headers={'Authorization': 'Bearer abc123'})
        data = json.loads(res.data)
        self.assertEqual(data['email'], 'foo@bar.com')
        self.assertEqual(user.email, 'foo@bar.com')

    @patch('app.models.User.check_token')
    def test_delete_user(self, mock_check_token):
        user = User(email='test@test.com')
        db.session.add(user)
        db.session.commit()
        mock_check_token.return_value = User.query.first()
        res = self.client.delete('/api/users/1',
                                 query_string={"export": False},
                                 headers={'Authorization': 'Bearer abc123'})
        self.assertEqual(res.status_code, 204)
        self.assertEqual('<User None>', str(User.query.first()))

    @patch('app.models.User.check_token')
    def test_enable_add_by_email(self, mock_check_token):
        user = User(email='test@test.com')
        db.session.add(user)
        db.session.commit()
        mock_check_token.return_value = User.query.first()

        self.assertIsNone(user.add_by_email)

        res = self.client.get('/api/users/1/enable_email',
                              headers={'Authorization': 'Bearer abc123'})
        self.assertEqual(res.status_code, 200)
        self.assertIsNotNone(user.add_by_email)

    @patch('app.models.User.check_token')
    def test_approved_senders(self, mock_check_token):
        user = User(email='test@test.com')
        db.session.add(user)
        db.session.commit()
        mock_check_token.return_value = User.query.first()

        self.assertIsNone(user.add_by_email)

        res = self.client.get('/api/users/1/senders',
                              headers={'Authorization': 'Bearer abc123'})
        self.assertEqual(res.status_code, 200)
        self.assertEqual([], user.approved_senders.all())
        res = self.client.get('/api/users/1/senders',
                              headers={'Authorization': 'Bearer abc123'})
        self.assertEqual(res.status_code, 200)
        self.assertEqual([], user.approved_senders.all())

        res = self.client.post('api/users/1/senders',
                               json={"email": "john@smith.com"},
                               headers={'Authorization': 'Bearer abc123'})
        self.assertEqual(res.status_code, 201)
        self.assertEqual(json.loads(res.data)['email'], 'john@smith.com')

        res = self.client.get('/api/users/1/senders',
                              headers={'Authorization': 'Bearer abc123'})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(['john@smith.com'], [str(sender) for sender in user.approved_senders.all()])

    @patch('app.models.User.check_token')
    def test_get_user_comms(self, mock_check_token):
        user = User(email='test@test.com')
        db.session.add(user)
        db.session.commit()
        comms = Comms(user_id=user.id)
        db.session.add(comms)
        db.session.commit()
        mock_check_token.return_value = User.query.first()

        res = self.client.get('/api/users/1/comms',
                              headers={'Authorization': 'Bearer abc123'})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(json.loads(res.data), comms.to_dict())

    @patch('app.models.User.check_token')
    def test_update_user_comms(self, mock_check_token):
        user = User(email='test@test.com')
        db.session.add(user)
        db.session.commit()
        comms = Comms(user_id=user.id)
        db.session.add(comms)
        db.session.commit()
        mock_check_token.return_value = User.query.first()

        self.assertEqual(comms.educational, True)
        res = self.client.patch('/api/users/1/comms',
                                json={'educational': False},
                                headers={'Authorization': 'Bearer abc123'})

        self.assertEqual(res.status_code, 200)
        self.assertEqual(comms.educational, False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
