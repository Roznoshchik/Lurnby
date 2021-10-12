from datetime import datetime, timedelta
import random
from flask_login import current_user

# 0 - 1 day
# 1 - 3 days
# 2 - 7 days
# 3 - 14 days
# 4 - 30 days
# 5 - 90 days
# 6 - 180 days
# 7 - 365 days

def get_time_delta(tier):
    if tier == 0:
        time = timedelta(days=1)
    if tier == 1:
        time = timedelta(days=3)
    if tier == 2:
        time = timedelta(days=7)
    if tier == 3:
        time = timedelta(days=14)
    if tier == 4:
        time = timedelta(days=30)
    if tier == 5:
        time = timedelta(days=90)
    if tier == 6:
        time = timedelta(days=180)
    if tier == 7:
        time = timedelta(days=365)

    return time


def check_for_review(highlight, tier):
    today = datetime.today()
    reviewed = highlight.review_date
    time = get_time_delta(tier)

    if today - reviewed > time:
        return True 
    
    return False


def order_highlights(highlights):
    tier0 = []
    tier1 = []
    tier2 = []
    tier3 = []
    tier4 = []
    tier5 = []
    tier6 = []
    tier7 = []
    
    #highlights = user.highlights.filter_by(archived=False).all()
    random.shuffle(highlights)
    count = current_user.review_count

    for h in highlights:
        if h.review_schedule == 0:
            if len(tier0) < count:
                if check_for_review(h, h.review_schedule):
                    tier0.append(h)
        if h.review_schedule == 1:
            if len(tier1) < count:
                if check_for_review(h, h.review_schedule):
                    tier1.append(h)
        if h.review_schedule == 2:
            if len(tier2) < count:
                if check_for_review(h, h.review_schedule):
                    tier2.append(h)
        if h.review_schedule == 3:
            if len(tier3) < count:
                if check_for_review(h, h.review_schedule):
                    tier3.append(h)
        if h.review_schedule == 4:
            if len(tier4) < count:
                if check_for_review(h, h.review_schedule):
                    tier4.append(h)
        if h.review_schedule == 5:
            if len(tier5) < count:
                if check_for_review(h, h.review_schedule):
                    tier5.append(h)
        if h.review_schedule == 6:
            if len(tier6) < count:
                if check_for_review(h, h.review_schedule):
                    tier6.append(h)
        if h.review_schedule == 7:
            if len(tier7) < count:
                if check_for_review(h, h.review_schedule):
                    tier7.append(h)
    
    tiers = [tier0, tier1, tier2, tier3, tier4, tier5, tier6, tier7]

    return tiers