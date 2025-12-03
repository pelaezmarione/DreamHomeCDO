# auth_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import get_main_connection

bp = Blueprint("auth", __name__)

@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_main_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT admin_id, email_address, password_hash, role, branch_key
            FROM Admin
            WHERE email_address = %s
        """, (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if not user or user["password_hash"] != password:
            flash("Invalid email or password", "error")
            return redirect(url_for("dashboard"))


        session.clear()
        session["user_id"] = user["admin_id"]
        session["role"] = user["role"]
        session["branch_key"] = user["branch_key"]

        if user["role"] == "admin":
            return redirect(url_for("admin.dashboard"))
        else:
            return redirect(url_for("branch.dashboard"))

    return render_template("login.html")

@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))

