import datetime

mock_articles = [
    {
        "user_id": 1,
        "title": "foo",
        "content": "<p>alabama arkansas, I do love my ma and pa</p>",
        "notes": "<p>This is a note</p>",
        "reflection": "<p>This is a reflection</p>",
        "archived": False,
        "done": True,
        "unread": False,
        "date_read": datetime.datetime(2023, 1, 6, 0, 33, 5, 792506),
        "tags": ["banana"],
    },
    {
        "user_id": 1,
        "title": "bar",
        "content": "<p>At first I was afraid, I was petrified, thinking I could never love again</p>",
        "archived": False,
        "done": False,
        "unread": True,
        "date_read": datetime.datetime(2023, 1, 10, 0, 33, 5, 792506),
        "tags": ["banana"],
    },
    {
        "user_id": 1,
        "title": "baz",
        "content": "<p>I just can't get enough</p>",
        "archived": False,
        "done": False,
        "unread": False,
        "date_read": datetime.datetime(2023, 1, 11, 0, 33, 5, 792506),
        "tags": ["peaches"],
    },
    {
        "user_id": 1,
        "title": "baba",
        "content": "All around me are familiar places",
        "archived": False,
        "done": False,
        "unread": False,
        "date_read": datetime.datetime(2023, 1, 22, 0, 33, 5, 792506),
        "tags": ["pears"],
    },
    {
        "user_id": 1,
        "title": "kazoo",
        "content": "You are my sunshine",
        "archived": True,
        "done": False,
        "unread": False,
        "date_read": datetime.datetime(2023, 1, 12, 0, 33, 5, 792506),
        "tags": ["peaches"],
    },
]

mock_tags = ["banana", "peaches", "pears", "strawberries"]

mock_highlight = {
    "note": "foobarbaz",
    "text": "alabama arkansaw, I do love my ma and pa",
    "prompt": "This is a prompt",
}
