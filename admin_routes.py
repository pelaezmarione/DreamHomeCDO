# admin_routes.py
from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from db import get_main_connection

bp = Blueprint("admin", __name__)

def require_admin():
    return session.get("role") == "admin"

@bp.route("/dashboard")
def dashboard():
    if not require_admin():
        return redirect(url_for("auth.login"))
    conn = get_main_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM Branch")
    branches_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM Admin")
    users_count = cur.fetchone()[0]

    cur.close()
    conn.close()
    return render_template("admin_dashboard.html",
                           branches_count=branches_count,
                           users_count=users_count)

@bp.route("/branches", methods=["GET", "POST"])
def branches():
    if not require_admin():
        return redirect(url_for("auth.login"))
    conn = get_main_connection()
    cur = conn.cursor(dictionary=True)

    if request.method == "POST":
        branch_key = request.form["branch_key"]
        branch_name = request.form["branch_name"]
        street = request.form["street"]
        barangay = request.form["barangay"]
        contact_number = request.form["contact_number"]
        cur2 = conn.cursor()
        cur2.execute("""
            INSERT INTO Branch (branch_key, branch_name, street, barangay, contact_number, date_created)
            VALUES (%s,%s,%s,%s,%s,NOW())
        """, (branch_key, branch_name, street, barangay, contact_number))
        conn.commit()
        cur2.close()
        flash("Branch added.", "success")

    cur.execute("SELECT * FROM Branch")
    branches = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("branches.html", branches=branches)

@bp.route("/users", methods=["GET", "POST"])
def users():
    if not require_admin():
        return redirect(url_for("auth.login"))
    conn = get_main_connection()
    cur = conn.cursor(dictionary=True)

    if request.method == "POST":
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        email = request.form["email_address"]
        password = request.form["password"]
        role = request.form["role"]
        branch_key = request.form.get("branch_key") or None

        cur2 = conn.cursor()
        cur2.execute("""
            INSERT INTO Admin (first_name,last_name,email_address,password_hash,role,branch_key,account_created)
            VALUES (%s,%s,%s,%s,%s,%s,NOW())
        """, (first_name, last_name, email, password, role, branch_key))
        conn.commit()
        cur2.close()
        flash("User added.", "success")

    cur.execute("SELECT * FROM Admin")
    users = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("users.html", users=users)
