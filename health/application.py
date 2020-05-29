import os
import csv
from datetime import date, datetime
from cs50 import SQL
from cs50 import get_string
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///health.db")


@app.route("/",methods=["GET", "POST"])
@login_required
def index():
    if request.method == "GET":
        data = db.execute("SELECT * FROM data WHERE userid = :userid", userid = session["user_id"])
        read = db.execute("SELECT * FROM weight WHERE wid = :wid", wid = session["user_id"])

        return render_template("index.html", data = data, username = session["username"], read = read)
    else:
        data = db.execute("SELECT * FROM data WHERE userid = :userid", userid = session["user_id"])
        weight = request.form.get("weight")
        day = date.today()
        now = datetime.now()
        time = now.strftime("%H:%M:%S")
        db.execute("INSERT INTO weight (wid,weight,date,time) VALUES (:wid, :weight, :date, :time)",wid = session["user_id"], weight = weight, date = day, time = time)
        read = db.execute("SELECT * FROM weight WHERE wid = :wid", wid = session["user_id"])
        return render_template("index.html", data = data, username = session["username"], read = read)



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        re_password = request.form.get("re_password")
        if password != re_password:
            return apology("Both passwords not matched", 403)
        rows = db.execute("SELECT username FROM users WHERE username = :username", username=username)
        hash_password = generate_password_hash(password)
        if rows:
            return apology("Username already exists", 403)
        else:
            db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash_password)", username = username, hash_password = hash_password)
            flash("Registration successful")
            return redirect("/")
    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        flash("Login Successful!!")
        session["username"] = (request.form.get("username"))
        # Redirect user to home page
        return redirect("/")
        # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/bmi", methods=["GET", "POST"])
@login_required
def bmi():
    if request.method == "GET":
        return render_template("bmi.html")
    else:
        height = float(request.form.get("height"))
        weight = float(request.form.get("weight"))
        if (height < 0 or weight < 0):
            flash("Please enter positive value")
            return redirect("/bmi")
        if (height > 7):
            flash("Please enter valid height")
            return redirect("/bmi")
        newheight = height * 12 * 0.025
        bmical = round(weight / (newheight * newheight),1)
        present = db.execute("SELECT userid FROM data where userid = :user_id", user_id = session["user_id"])
        if present:
            db.execute("UPDATE data SET bmi = :bmi, height = :height, weight = :weight WHERE userid = :user_id", bmi = bmical, height = round((newheight * 100),2), weight = weight, user_id = session["user_id"])
        else:
            db.execute("INSERT INTO data (userid, bmi, weight, height) VALUES (:userid, :bmi, :weight, :height)", userid = session["user_id"], bmi = bmical, weight = weight, height = round((newheight * 100),2))
        return render_template("newbmi.html",height = height, weight = weight, calbmi = bmical,newheight = round((newheight * 100),2))

@app.route("/whr", methods=["GET", "POST"])
@login_required
def whr():
    if request.method == "GET":
        return render_template("whr.html")
    else:
        hip = float(request.form.get("hip"))
        waist = float(request.form.get("waist"))
        if (hip < 0 or waist < 0):
            flash("Please enter positive value")
            return redirect("/whr")

        hip = hip * 2.54
        waist = waist * 2.54
        whrcal = round((waist / hip),2)
        present = db.execute("SELECT userid FROM data where userid = :user_id", user_id = session["user_id"])
        if present:
            db.execute("UPDATE data SET whr = :whr WHERE userid = :user_id", whr = whrcal, user_id = session["user_id"])
        else:
            db.execute("INSERT INTO data (userid, whr) VALUES (:userid, :whr)", userid = session["user_id"], whr = whrcal)
        return render_template("whrcal.html",hip=hip, waist=waist, whr = whrcal)

@app.route("/bmr", methods=["GET", "POST"])
@login_required
def bmr():
    if request.method == "GET":
        return render_template("bmr.html")
    else:
        gender = request.form.get("gender")
        age = int(request.form.get("age"))
        height = float(request.form.get("height"))
        weight = float(request.form.get("weight"))
        if(gender == 'male'):
            calbmr = 5 + (10 * weight) + (6.25 * height) - (5 * age)
            carbmin = calbmr * 0.45
            carbmax = calbmr * 0.65
            protmin = calbmr * 0.10
            protmax = calbmr * 0.35
            fatmin = calbmr * 0.20
            fatmax = calbmr * 0.35
            sed = calbmr * 1.30
            light = calbmr * 1.55
            moderate = calbmr * 1.65
            intense = calbmr * 1.80
            very = calbmr * 2
            present = db.execute("SELECT userid FROM data where userid = :user_id", user_id = session["user_id"])
            if present:
                db.execute("UPDATE data SET bmr = :bmr, age = :age WHERE userid = :user_id", bmr = calbmr, age = age, user_id = session["user_id"])
            else:
                db.execute("INSERT INTO data (userid, whr, age) VALUES (:userid, :whr, :age)", userid = session["user_id"], whr = round(calbmr), age=age)
            return render_template("bmrcal.html", calbmr = round(calbmr), sed=round(sed), carbmin = round(carbmin), carbmax = round(carbmax),
                                    light=round(light), moderate=round(moderate), protmin = round(protmin), protmax = round(protmax),
                                    intense = round(intense),  very = round(very), fatmin = round(fatmin), fatmax = round(fatmax))
        else:
            calbmr = ((10 * weight) + (6.25 * height) - (5 * age)) - 161
            carbmin = calbmr * 0.45
            carbmax = calbmr * 0.65
            protmin = calbmr * 0.10
            protmax = calbmr * 0.35
            fatmin = calbmr * 0.20
            fatmax = calbmr * 0.35
            sed = calbmr * 1.30
            light = calbmr * 1.55
            moderate = calbmr * 1.65
            intense = calbmr * 1.80
            very = calbmr * 2
            present = db.execute("SELECT userid FROM data where userid = :user_id", user_id = session["user_id"])
            if present:
                db.execute("UPDATE data SET bmr = :bmr WHERE userid = :user_id", bmr = calbmr, user_id = session["user_id"])
            else:
                db.execute("INSERT INTO data (userid, whr) VALUES (:userid, :whr)", userid = session["user_id"], whr = round(calbmr))
            return render_template("bmrcal.html", calbmr = round(calbmr), sed=round(sed), carbmin = round(carbmin), carbmax = round(carbmax),
                                    light=round(light), moderate=round(moderate), protmin = round(protmin), protmax = round(protmax),
                                    intense = round(intense),  very = round(very), fatmin = round(fatmin), fatmax = round(fatmax))


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()
    flash("You logged out successfully")
    # Redirect user to login form
    return redirect("/")




@app.route("/fun")
@login_required
def fun():
    return render_template("fun.html")



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
