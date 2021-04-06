from datetime import datetime
from flask import Flask, render_template, abort, jsonify, request, redirect, url_for, g, flash
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
import pdb
import sqlite3

from model import db, save_db

app = Flask(__name__)
app.config["SECRET_KEY"] = "secretkey"


class NewItemForm(FlaskForm):
    title       = StringField("Title")
    price       = StringField("Price")
    description = TextAreaField("Description")
    submit      = SubmitField("Submit")

@app.route('/')
def home():
    conn = get_db()
    c = conn.cursor()

    items_from_db = c.execute("""SELECT
                    i.id, i.title, i.description, i.price, i.image, c.name, s.name
                    FROM
                    items AS i
                    INNER JOIN categories AS c ON i.category_id = c.id
                    INNER JOIN subcategories AS s ON i.subcategory_id = s.id
                    ORDER BY i.id DESC
    """)

    items = []
    for row in items_from_db:
        item = {
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "price": row[3],
            "image": row[4],
            "category": row[5],
            "subcategory": row[6]
        }
        items.append(item)

    
    return render_template("home.html", items=items)


@app.route("/item/new", methods=["GET", "POST"])
def new_item():
    conn = get_db()
    c = conn.cursor()
    form = NewItemForm()

    #pdb.set_trace()
    if request.method == "POST":
        # Process the form data
        c.execute("""INSERT INTO items
                    (title, description, price, image, category_id, subcategory_id)
                    VALUES(?,?,?,?,?,?)""",
                    (
                        form.title.data,
                        form.description.data,
                        float(form.price.data),
                        "",
                        1,
                        1
                    )
        )
        conn.commit()
    
        #print("Form data:") - terminal processing
        #print("Title: {}, Description: {}".format(
        #    request.form.get("title"), request.form.get("description")
        #))
        # Redirect to some page
        flash("Item {} has been successfully submited".format(request.form.get("title")), "success")
        return redirect(url_for("home"))
    return render_template("new_item.html", form=form)

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect("db/globomantics.db")
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


@app.route('/welcome')
def welcome():
    return render_template(
        "welcome.html",
        cards=db
        
        )


@app.route("/card/<int:index>")
def card_view(index):
    try:
        card = db[index]
        return render_template("card.html",
             card=card,
             index=index,
             max_index=len(db)-1)
    except IndexError:
        abort(404)
counter = 0

@app.route('/counter')
def counter():
    global counter
    counter += 1
    return "This page has been visited " + str(counter) + " times"


@app.route('/date')
def date():
    
    return "This page was served at " + str(datetime.now()) 

@app.route("/api/card/")
def api_card_list():
    return db #don't do jsonify(db) 


@app.route('/add_card', methods=["GET", "POST"])
def add_card():
    if request.method == "POST":
        # form has been submitted, process data
        card = { "question": request.form['question'],
        "answer": request.form['answer']}
        db.append(card)
        save_db
        return redirect(url_for('card_view', index=len(db)-1))
    else:
        return render_template("add_card.html")

@app.route('/remove_card/<int:index>', methods=["GET", "POST"])
def remove_card(index):
    try:
        if request.method == "POST":
            del db[index]
            save_db()
            return redirect(url_for('welcome'))
        else:    
            return render_template("remove_card.html", card=db[index])
    except IndexError:
        abort(404)

@app.route('/api/card/<int:index>')
def api_card_detail(index):
    try:
        return db[index]
    except IndexError:
        abort(404)


