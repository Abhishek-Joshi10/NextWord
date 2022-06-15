from flask import Flask, redirect, url_for, render_template, request, session, flash
from keras.models import load_model
import pickle
from nltk.tokenize import RegexpTokenizer
import numpy as np
import heapq
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from transformers import pipeline

#importing library
#from transformers import BertTokenizer, TFBertModel
#defining tokenizer
#tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
#instantiating the model
#model = TFBertModel.from_pretrained("bert-base-uncased")
#text = "What is your name?"
#extracting features
#encoded_input = tokenizer(text, return_tensors='tf')
#model(encoded_input)

model = pipeline('fill-mask', model='bert-base-uncased')

application = Flask(__name__)
app = application
app.secret_key = "esra"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///history.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class users(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user = db.Column(db.String(100))

    def __init__(self, user):
        self.user = user


class history(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer())
    date = db.Column(db.DateTime, default=datetime.utcnow)
    text = db.Column(db.String(100))
    choice = db.Column(db.String(100))

    def __init__(self, user_id, date, text, choice):
        self.user_id = user_id
        self.date = date
        self.text = text
        self.choice = choice


@app.route("/", methods=["POST", "GET"])
def home():
    if request.method == "POST":
        username_form = request.form["username"]
        session["user"] = username_form

        found_user = users.query.filter_by(user=username_form).first()

        if found_user:
            #            session["userID"] = found_user.id
            flash("Login Successfull!")
        else:
            usr = users(username_form)
            db.session.add(usr)
            db.session.commit()
            found_user = users.query.filter_by(user=username_form).first()
        #            session["userID"] = found_user.id

        return redirect(url_for("main", text="a"))
    else:
        #        if "user" in session:
        #            flash("Already logged in!")
        return render_template("index.html")


@app.route("/main/<text>", methods=["POST", "GET"])
def main(text):
    if "user" in session:
        user = session["user"]
    if request.method == "POST":
        input_text = request.form["text"]
        input_ready = input_text + " " + "[MASK]" + "."
        pred = model(input_ready)
        return redirect(url_for("results", text=input_text, username=user, suggestions1=pred[0]['token_str'],
                                suggestions2=pred[1]['token_str'], suggestions3=pred[2]['token_str'],
                                suggestions4=pred[3]['token_str'], suggestions5=pred[4]['token_str']))
    else:
        flash("Login Successfull!")
        return render_template("main.html", username=user, text=text)


@app.route("/view")
def view():
    if "user" in session:
        user = session["user"]
    return render_template("view.html", values=users.query.all(), username=user)


@app.route("/user_history")
def user_history():
    if "user" in session:
        user = session["user"]
    found_user = users.query.filter_by(user=user).first()
    return render_template("user_history.html", values=history.query.filter_by(user_id=found_user.id).all(),
                           username=user)


@app.route("/results/<text>/<username>/<suggestions1>/<suggestions2>/<suggestions3>/<suggestions4>/<suggestions5>",
           methods=["POST", "GET"])
def results(text, username, suggestions1, suggestions2, suggestions3, suggestions4, suggestions5):
    if request.method == "POST" and request.form['suggestions']:
        updated_text = text + " " + request.form['suggestions']

        # saving user choice in history.db
        found_user = users.query.filter_by(user=username).first()
        curr_date = datetime.now()
        history_input = history(found_user.id, curr_date, text, request.form['suggestions'])
        db.session.add(history_input)
        db.session.commit()

        return redirect(url_for("main", text=updated_text))
    else:
        return render_template("results.html", text=text, username=username, suggestions1=suggestions1,
                               suggestions2=suggestions2, suggestions3=suggestions3, suggestions4=suggestions4,
                               suggestions5=suggestions5)


if __name__ == '__main__':
    db.create_all()
    app.run()
