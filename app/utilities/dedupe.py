from app.models import Article
u = None
# Finding duplicate articles

# this will print out articles that have 
# the same titles. for each match, it will print 2x -> 1,5 & 5,1
def dedupe(n):
    a = d[n]
    for key,value in d.items():
        if a == value and key != n:
            print(f'{key} <-> {n}')

articles = u.articles.all()
d = {}
for a in articles:
    d[a.id] = a.title

for k,v in d.items():
    dedupe(k)    


# get article, check title, 
# check highlight amount, see if it's already archived.
a = Article.query.filter_by(id=173).first()
a.title
a.highlights.count()
a.archived