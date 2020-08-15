import unittest
from app import create_app, db
from app.models import User, Highlight, Tag, Topic, highlights_topics
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'



class HighlightModelCase(unittest.TestCase):
    current_user=User.query.first()
    
    
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
        h1 = Highlight(text = "this is a highlight")
        h2 = Highlight(text = "This is a second highlight")
        t1 = Topic(title = "Canaries")
        t2 = Topic(title = "Bluejays")

        db.session.add_all([h1,h2,t1,t2])
        db.session.commit()

        self.assertEqual(h1.topics.all(), [])
        self.assertEqual(h2.topics.all(), [])

        h1.AddToTopic(t1)
        db.session.commit()
        
        self.assertTrue(h1.is_added(t1))
        self.assertEqual(h1.topics.count(), 1)
        self.assertEqual(h1.topics.first().title, 'Canaries')
        self.assertEqual(t1.highlights.count(), 1)
        self.assertEqual(t1.highlights.first().text, 'this is a highlight')

        h1.RemoveFromTopic(t1)
        db.session.commit()
        
        self.assertFalse(h1.is_added(t1))
        self.assertEqual(h1.topics.count(), 0)
        self.assertEqual(t1.highlights.count(), 0)


    def test_show_members(self):
        h1 = Highlight(text = "this is a highlight")
        h2 = Highlight(text = "This is a second highlight")
        h3 = Highlight(text = "This is a third highlight")
        h4 = Highlight(text = "This is a fourth highlight")


        t1 = Topic(title = "Canaries")
        t2 = Topic(title = "Bluejays")
        t3 = Topic(title = "Crows")
        t4 = Topic(title = "Ravens")

        db.session.add_all([h1,h2,h3,h4,t1,t2,t3,t4])
        db.session.commit()

        #h1 in 2 lists - Canaries + Crows
        h1.AddToTopic(t1)
        h1.AddToTopic(t3)
        
        #h2 in 1 list - Bluejays
        h2.AddToTopic(t2)
        
        #h3 in all lists - Canaries, Bluejays, Crows, Ravens
        h3.AddToTopic(t1)
        h3.AddToTopic(t2)
        h3.AddToTopic(t3)
        h3.AddToTopic(t4)
        #h4 not in any lists

        db.session.commit()

        m1 = h1.in_topics().all()
        m2 = h2.in_topics().all()
        m3 = h3.in_topics().all()
        m4 = h4.in_topics().all()

        nm1 = h1.not_in_topics()
        nm2 = h2.not_in_topics()
        nm3 = h3.not_in_topics()
        nm4 = h4.not_in_topics() 

        self.assertEqual(m1, [t1, t3])
        self.assertEqual(nm1, [t2, t4])
        
        self.assertEqual(m2, [t2])
        self.assertEqual(nm2, [t1, t3, t4])
        
        self.assertEqual(m3, [t1, t2, t3, t4])
        self.assertEqual(nm3, [])
       
        self.assertEqual(m4, [])
        self.assertEqual(nm4, [t1, t2, t3, t4])

if __name__ == "__main__":
    unittest.main(verbosity=2)