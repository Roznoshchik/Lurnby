from app import app
from flask import flash, redirect, url_for, render_template, request
from app.forms import URLForm, LoginForm
from app.pulltext import pull_text

@app.route("/", methods=['GET','POST'])
@app.route("/index", methods=['GET','POST'])
def index():
    form = URLForm()
    if form.validate_on_submit():
        

        if request.method =='POST':
            url = request.form['url']
            text = pull_text(url)
            return render_template('text.html', title =text["title"], author = text["byline"], content=text["plain_content"])
            
        return redirect(url_for('index'))

    return render_template('index.html', title="Elegant Reader", form=form)
 
