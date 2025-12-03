from flask import Flask, redirect, url_for, session, render_template, request
from datetime import timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_main_connection

app = Flask(__name__)
app.secret_key = "super-secret-key"
app.permanent_session_lifetime = timedelta(hours=4)

import auth_routes
import branch_routes
import admin_routes

app.register_blueprint(auth_routes.bp, url_prefix="/")
app.register_blueprint(branch_routes.bp, url_prefix="/branch")
app.register_blueprint(admin_routes.bp, url_prefix="/admin")


# HOME ROUTE
@app.route("/")
def home():
    role = session.get("role")
    if role == "admin":
        return redirect(url_for("admin.dashboard"))
    elif role in ("manager", "staff"):
        return redirect(url_for("branch.dashboard"))
    return redirect(url_for("auth.login"))



# ---------------------- USER SYSTEM ----------------------

@app.route("/user/register", methods=["GET", "POST"])
def user_register():
    if request.method == "POST":
        fullname = request.form["fullname"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]

        hashed = generate_password_hash(password)

        conn = get_main_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO users (fullname, email, password, phone)
            VALUES (%s, %s, %s, %s)
        """, (fullname, email, hashed, phone))

        conn.commit()
        cur.close()
        conn.close()

        return redirect("/user/login")

    return render_template("user_register.html")


@app.route("/user/login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_main_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["user_id"]
            session["user_name"] = user["fullname"]
            return redirect("/user/home")

        return render_template("user_login.html", error="Invalid login")

    return render_template("user_login.html")


@app.route("/user/logout")
def user_logout():
    session.clear()
    return redirect("/user/login")


@app.route("/user/home")
def user_home():
    if "user_id" not in session:
        return redirect("/user/login")

    conn = get_main_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT property_id, title, barangay, price FROM Property")
    properties = cur.fetchall()

    return render_template("user_home.html", properties=properties, username=session["user_name"])


@app.route("/user/property/<int:property_id>")
def user_property(property_id):
    if "user_id" not in session:
        return redirect("/user/login")

    conn = get_main_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM Property WHERE property_id=%s", (property_id,))
    prop = cur.fetchone()

    return render_template("user_property.html", property=prop)



# END PROGRAM
if __name__ == "__main__":
    app.run(debug=True)
