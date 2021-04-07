from datetime import datetime
from flask import Flask, render_template, abort, jsonify, request, redirect, url_for, g, flash
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField, DecimalField
from wtforms.validators import InputRequired, DataRequired, Length
import pdb
import sqlite3

from model import db, save_db

app = Flask(__name__)
app.config["SECRET_KEY"] = "secretkey"

class ItemForm(FlaskForm):
    title       = StringField("Title", validators=[InputRequired("Input is required!"), DataRequired("Data is required!"), Length(min=5, max=20, message="Input must be between 5 and 20 characters long")])
    price       = DecimalField("Price")
    description = TextAreaField("Description", validators=[InputRequired("Input is required!"), DataRequired("Data is required!"), Length(min=4, max=40, message="Description must be between 4 and 40 characters long")])
    

class NewItemForm(ItemForm):
    title       = StringField("Title", validators=[InputRequired("Input is required!"), DataRequired("Data is required!"), Length(min=5, max=20, message="Input must be between 5 and 20 characters long")])
    price       = DecimalField("Price")
    description = TextAreaField("Description", validators=[InputRequired("Input is required!"), DataRequired("Data is required!"), Length(min=4, max=40, message="Description must be between 4 and 40 characters long")])
    category    = SelectField("Category", coerce=int)
    subcategory = SelectField("Subcategory", coerce=int)
    submit      = SubmitField("Submit")

class EditItemForm(ItemForm):
    submit      = SubmitField("Update Item")

class DeleteItemForm(FlaskForm):
    submit      = SubmitField("Delete item")

@app.route("/item/<int:item_id>/edit", methods=["GET", "POST"])
def edit_item(item_id):
    conn = get_db()
    c = conn.cursor()
    item_from_db = c.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    row = c.fetchone()
    try:
        item = {
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "price": row[3],
            "image": row[4],
        }
    except:
        item = {}
    
    if item:
        form = EditItemForm()
        if form.validate_on_submit():
            c.execute("""UPDATE items SET
            title = ?, description = ?, price = ?
            WHERE id = ?""",
                (
                    form.title.data,
                    form.description.data,
                    float(form.price.data),
                    item_id                
                )
            )
            conn.commit()

            flash("Item {} has been successfully updated".format(form.title.data), "success")
            return redirect(url_for("item", item_id=item_id))

        form.title.data         = item["title"]
        form.description.data   = item["description"]
        form.price.data         = item["price"]

        if form.errors:
            flash("{}".format(form.errors), "danger")
        return render_template("edit_item.html", item=item, form=form)

    return redirect(url_for("home"))

@app.route("/item/<int:item_id>/delete", methods=["POST"])
def delete_item(item_id):
    conn = get_db()
    c = conn.cursor()

    item_from_db = c.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    row = c.fetchone()
    try:
        item = {
            "id": row[0],
            "title": row[1]
        }
    except:
        item = {}
    if item:
        c.execute("DELETE FROM items WHERE id = ?", (item_id,))
        conn.commit()

        flash("Item {} has been successfully deleted.".format(item["title"])),
    else:
        flash("This item does not exist.", "danger")
    
    return redirect(url_for("home"))



@app.route("/item/<int:item_id>")
def item(item_id):
    c = get_db().cursor()
    item_from_db = c.execute("""SELECT
                    i.id, i.title, i.description, i.price, i.image, c.name, s.name
                    FROM
                    items AS i
                    INNER JOIN categories AS c ON i.category_id = c.id
                    INNER JOIN subcategories AS s ON i.subcategory_id = s.id
                    WHERE i.id = ?""",
                    (item_id,)
    )
    row = c.fetchone()

    try:
        item = {
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "price": row[3],
                "image": row[4],
                "category": row[5],
                "subcategory": row[6]
            }
    except:
        item = {}    

    if item:
        deleteItemForm = DeleteItemForm()
        return render_template("item.html", item=item, deleteItemForm=deleteItemForm)
    return redirect(url_for("home"))


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

    c.execute("SELECT id, name FROM categories")
    categories = c.fetchall()
    # [(1, 'Food'), (2, 'Technology'), (3, 'Books')]
    form.category.choices = categories

    c.execute("""SELECT id, name FROM subcategories
                WHERE category_id = ?""",
                (1,)
    )
    subcategories = c.fetchall()
    form.subcategory.choices = subcategories


    #pdb.set_trace()
    if form.validate_on_submit():
        # Process the form data
        c.execute("""INSERT INTO items
                    (title, description, price, image, category_id, subcategory_id)
                    VALUES(?,?,?,?,?,?)""",
                    (
                        form.title.data,
                        form.description.data,
                        float(form.price.data),
                        "",
                        form.category.data,
                        form.subcategory.data
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

    if form.errors:
        flash("{}".format(form.errors), "danger")

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


