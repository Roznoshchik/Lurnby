from app import db
from app.models import Highlight, Topic


def createHighlightPrompts():
  highlights = Highlight.query.all()
  for highlight in highlights:
    flashcard = Topic.query.filter_by(title='flashcard').first()
    flashcards = Topic.query.filter_by(title='flashcards').first()
    
    if flashcard and highlight.is_added_topic(flashcard):
      highlight.prompt = highlight.text
      highlight.text = highlight.note
      continue
    elif flashcards and highlight.is_added_topic(flashcards):
      highlight.prompt = highlight.text
      highlight.text = highlight.note
      continue
    else:
      highlight.user.launch_task('create_recall_text', 'Creating highlight recall text', highlight.id)

      # create_recall_text(highlight.id)

  db.session.commit()