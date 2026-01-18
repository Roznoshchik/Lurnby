from app import db
from app.models import User, Highlight, Tag, Article
from tests.conftest import BaseTestCase


class TagModelCase(BaseTestCase):

    def test_add_removing_tags(self):
        u = User(username="john")
        db.session.add(u)

        h1 = Highlight(text="this is a highlight", user_id=u.id, archived=False)
        h2 = Highlight(text="This is a second highlight", user_id=u.id, archived=False)
        a1 = Article(title="Breaking Breaking!", user_id=u.id, archived=False)
        a2 = Article(title="Read all about it!", user_id=u.id, archived=False)
        tag1 = Tag(name="tag1", user_id=u.id, archived=False)
        tag2 = Tag(name="tag2", user_id=u.id, archived=False)

        db.session.add_all([h1, h2, a1, a2, tag1, tag2])
        db.session.commit()

        self.assertEqual(a1.tags, [])
        self.assertEqual(a2.tags, [])

        self.assertEqual(h1.tags, [])
        self.assertEqual(h2.tags, [])

        a1.add_tag(tag1)
        h1.add_tag(tag1)
        db.session.commit()

        self.assertTrue(a1.is_added_tag(tag1))
        self.assertEqual(len(a1.tags), 1)
        self.assertEqual(a1.tags[0].name, "tag1")
        self.assertEqual(len(tag1.articles), 1)
        self.assertEqual(tag1.articles[0].title, "Breaking Breaking!")

        self.assertTrue(h1.is_added_tag(tag1))
        self.assertEqual(len(h1.tags), 1)
        self.assertEqual(h1.tags[0].name, "tag1")
        self.assertEqual(len(tag1.highlights), 1)
        self.assertEqual(tag1.highlights[0].text, "this is a highlight")

        a1.remove_tag(tag1)
        h1.remove_tag(tag1)
        db.session.commit()

        self.assertFalse(a1.is_added_tag(tag1))
        self.assertEqual(len(a1.tags), 0)

    def test_show_members(self):
        u = User(username="john")
        db.session.add(u)
        u = User.query.first()

        h1 = Highlight(text="this is a highlight", user_id=u.id, archived=False)
        h2 = Highlight(text="This is a second highlight", user_id=u.id, archived=False)
        h3 = Highlight(text="this is a third highlight", user_id=u.id, archived=False)
        h4 = Highlight(text="This is a fourth highlight", user_id=u.id, archived=False)

        a1 = Article(title="Breaking Breaking!", user_id=u.id, archived=False)
        a2 = Article(title="Read all about it!", user_id=u.id, archived=False)
        a3 = Article(title="You won't believe!", user_id=u.id, archived=False)
        a4 = Article(title="Top 10 Must See!", user_id=u.id, archived=False)

        tag1 = Tag(name="Lauma", user_id=u.id, archived=False)
        tag2 = Tag(name="Slavs", user_id=u.id, archived=False)
        tag3 = Tag(name="Major", user_id=u.id, archived=False)
        tag4 = Tag(name="Pablo", user_id=u.id, archived=False)

        db.session.add_all([h1, h2, h3, h4, a1, a2, a3, a4, tag1, tag2, tag3, tag4])
        db.session.commit()

        # in 2 tags
        a1.add_tag(tag1)
        a1.add_tag(tag3)
        h1.add_tag(tag1)
        h1.add_tag(tag3)

        # in 1 tag
        a2.add_tag(tag2)
        h2.add_tag(tag2)

        # in all tags
        a3.add_tag(tag1)
        a3.add_tag(tag2)
        a3.add_tag(tag3)
        a3.add_tag(tag4)
        h3.add_tag(tag1)
        h3.add_tag(tag2)
        h3.add_tag(tag3)
        h3.add_tag(tag4)

        # a4, h4 not in any tags

        db.session.commit()

        # Article tags
        self.assertCountEqual(a1.tags, [tag1, tag3])
        self.assertCountEqual(a1.not_in_tags(u), [tag2, tag4])
        self.assertCountEqual(a2.tags, [tag2])
        self.assertCountEqual(a2.not_in_tags(u), [tag1, tag3, tag4])
        self.assertCountEqual(a3.tags, [tag1, tag2, tag3, tag4])
        self.assertCountEqual(a3.not_in_tags(u), [])
        self.assertCountEqual(a4.tags, [])
        self.assertCountEqual(a4.not_in_tags(u), [tag1, tag2, tag3, tag4])

        # Highlight tags
        self.assertCountEqual(h1.tags, [tag1, tag3])
        self.assertCountEqual(h1.not_in_tags(u), [tag2, tag4])
        self.assertCountEqual(h2.tags, [tag2])
        self.assertCountEqual(h2.not_in_tags(u), [tag1, tag3, tag4])
        self.assertCountEqual(h3.tags, [tag1, tag2, tag3, tag4])
        self.assertCountEqual(h3.not_in_tags(u), [])
        self.assertCountEqual(h4.tags, [])
        self.assertCountEqual(h4.not_in_tags(u), [tag1, tag2, tag3, tag4])
