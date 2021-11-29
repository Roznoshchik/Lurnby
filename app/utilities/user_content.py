from app import db
from app.email import send_email
from app.models import Highlight, User, Message, Comms
import random
from datetime import datetime, timedelta
from calendar import timegm

import json
from flask import url_for, render_template, current_app

def get_recent_highlights():
    users = User.query.join(Comms, (Comms.user_id == User.id)).filter(Comms.highlights == True, User.deleted == False, User.test_account == False).all()
    today = datetime.utcnow()
    last_week = today - timedelta(days=7)
    #nine_am = datetime(today.year, today.month, today.day, 8, 53, 0, 0)
    # nine_am = datetime(today.year, today.month, today.day, 21, 7, 0, 0)
    # if today > nine_am:
    #     print('tomorrow')
    #     nine_am = nine_am + timedelta(days=1)
    # send_at = timegm(nine_am.utctimetuple())
    # headers = {'send_at': send_at}

    for u in users:

        msg = u.messages.filter(Message.name == 'recent highlights', Message.date <= last_week).first()
        if not msg:
            highlights = u.highlights.order_by(Highlight.created_date.desc()).filter(Highlight.review_date < last_week).all()
            recent = []
            if len(highlights) > 1:
                if len(highlights) < 6:
                    for h in highlights:
                        recent.append(h)
                        h.review_date = today
                else:   
                    for i in range(5):
                        num = random.randint(0, len(highlights) - 1 )
                        recent.append(highlights[num])
                        highlights[num].review_date = today   
                        highlights.remove(highlights[num])
                    
                send_email('[Lurnby] Your recent highlights',
                    sender=current_app.config['ADMINS'][0], recipients=[u.email],
                    text_body=render_template('email/content/recent_highlights.txt', highlights = recent),
                    html_body=render_template('email/content/recent_highlights.html', highlights = recent),
                    sync=True)
                msg = Message.add('recent highlights', u)
                db.session.add(msg)
                db.session.commit()
                #print(render_template('email/content/recent_highlights.html', highlights=recent))
            else: 
                print('no highlights qualified') 
            
    

def highlights_urls(highlights):
    print(render_template('email/content/recent_highlights.html', highlights=highlights))

    

