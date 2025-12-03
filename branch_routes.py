# branch_routes.py
from flask import Blueprint, render_template, session, redirect, url_for, request, flash, jsonify
from db import get_branch_connection

bp = Blueprint("branch", __name__)

def require_branch_login():
    return session.get("role") in ("manager", "staff")

def get_branch_conn_from_session():
    branch_key = session.get("branch_key")
    if not branch_key:
        raise ValueError("No branch_key in session")
    return get_branch_connection(branch_key), branch_key

# -------- Dashboard --------
@bp.route("/dashboard")
def dashboard():
    if not require_branch_login():
        return redirect(url_for("auth.login"))

    conn, branch_key = get_branch_conn_from_session()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM Property")
    properties_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM Property_Owner")
    owners_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM Customer")
    customers_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM Appointment")
    appointments_count = cur.fetchone()[0]

    cur.close()
    conn.close()

    return render_template(
        "branch_dashboard.html",
        branch_key=branch_key,
        properties_count=properties_count,
        owners_count=owners_count,
        customers_count=customers_count,
        appointments_count=appointments_count
    )

# ================= PROPERTIES =================

@bp.route("/properties")
def properties_list():
    if not require_branch_login():
        return redirect(url_for("auth.login"))
    conn, branch_key = get_branch_conn_from_session()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM Property")
    properties = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("properties_list.html", properties=properties, branch_key=branch_key)

@bp.route("/properties/add", methods=["GET", "POST"])
def properties_add():
    if not require_branch_login():
        return redirect(url_for("auth.login"))
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        price = request.form["price"]
        listing_type = request.form["listing_type"]
        barangay = request.form["barangay"]
        full_address = request.form["full_address"]
        status = request.form["status"]

        conn, _ = get_branch_conn_from_session()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Property (owner_id, title, description, price, listing_type,
                                  barangay, full_address, status, date_posted)
            VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, (title, description, price, listing_type, barangay, full_address, status))
        conn.commit()
        cur.close()
        conn.close()
        flash("Property added successfully.", "success")
        return redirect(url_for("branch.properties_list"))
    return render_template("properties_form.html", action="Add", prop=None)

@bp.route("/properties/<int:property_id>/edit", methods=["GET", "POST"])
def properties_edit(property_id):
    if not require_branch_login():
        return redirect(url_for("auth.login"))
    conn, _ = get_branch_conn_from_session()
    cur = conn.cursor(dictionary=True)

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        price = request.form["price"]
        listing_type = request.form["listing_type"]
        barangay = request.form["barangay"]
        full_address = request.form["full_address"]
        status = request.form["status"]

        cur.execute("""
            UPDATE Property
            SET title=%s, description=%s, price=%s, listing_type=%s,
                barangay=%s, full_address=%s, status=%s
            WHERE property_id=%s
        """, (title, description, price, listing_type, barangay, full_address, status, property_id))
        conn.commit()
        cur.close()
        conn.close()
        flash("Property updated.", "success")
        return redirect(url_for("branch.properties_list"))

    cur.execute("SELECT * FROM Property WHERE property_id = %s", (property_id,))
    prop = cur.fetchone()
    cur.close()
    conn.close()
    if not prop:
        flash("Property not found.", "error")
        return redirect(url_for("branch.properties_list"))
    return render_template("properties_form.html", action="Edit", prop=prop)

@bp.route("/properties/<int:property_id>/delete", methods=["POST"])
def properties_delete(property_id):
    if not require_branch_login():
        return redirect(url_for("auth.login"))
    conn, _ = get_branch_conn_from_session()
    cur = conn.cursor()
    cur.execute("DELETE FROM Property WHERE property_id = %s", (property_id,))
    conn.commit()
    cur.close()
    conn.close()
    flash("Property deleted.", "success")
    return redirect(url_for("branch.properties_list"))

# Simple JSON API for properties
@bp.route("/api/properties")
def properties_api():
    if not require_branch_login():
        return jsonify({"error": "unauthorized"}), 401
    conn, _ = get_branch_conn_from_session()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM Property")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data)

# ================= OWNERS =================

@bp.route("/owners")
def owners_list():
    if not require_branch_login():
        return redirect(url_for("auth.login"))
    conn, branch_key = get_branch_conn_from_session()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM Property_Owner")
    owners = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("owners_list.html", owners=owners, branch_key=branch_key)

@bp.route("/owners/add", methods=["GET", "POST"])
def owners_add():
    if not require_branch_login():
        return redirect(url_for("auth.login"))
    if request.method == "POST":
        first_name = request.form["first_name"]
        middle_name = request.form.get("middle_name", "")
        last_name = request.form["last_name"]
        contact_number = request.form["contact_number"]
        email_address = request.form["email_address"]
        barangay = request.form["barangay"]

        conn, _ = get_branch_conn_from_session()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Property_Owner (
                first_name, middle_name, last_name, contact_number,
                email_address, barangay, password_hash, date_registered
            ) VALUES (%s,%s,%s,%s,%s,%s,'default', NOW())
        """, (first_name, middle_name, last_name, contact_number, email_address, barangay))
        conn.commit()
        cur.close()
        conn.close()
        flash("Owner added.", "success")
        return redirect(url_for("branch.owners_list"))

    return render_template("owners_form.html", action="Add", owner=None)

@bp.route("/owners/<int:owner_id>/edit", methods=["GET", "POST"])
def owners_edit(owner_id):
    if not require_branch_login():
        return redirect(url_for("auth.login"))
    conn, _ = get_branch_conn_from_session()
    cur = conn.cursor(dictionary=True)

    if request.method == "POST":
        first_name = request.form["first_name"]
        middle_name = request.form.get("middle_name", "")
        last_name = request.form["last_name"]
        contact_number = request.form["contact_number"]
        email_address = request.form["email_address"]
        barangay = request.form["barangay"]

        cur.execute("""
            UPDATE Property_Owner
            SET first_name=%s, middle_name=%s, last_name=%s,
                contact_number=%s, email_address=%s, barangay=%s
            WHERE owner_id=%s
        """, (first_name, middle_name, last_name, contact_number, email_address, barangay, owner_id))
        conn.commit()
        cur.close()
        conn.close()
        flash("Owner updated.", "success")
        return redirect(url_for("branch.owners_list"))

    cur.execute("SELECT * FROM Property_Owner WHERE owner_id=%s", (owner_id,))
    owner = cur.fetchone()
    cur.close()
    conn.close()
    if not owner:
        flash("Owner not found.", "error")
        return redirect(url_for("branch.owners_list"))
    return render_template("owners_form.html", action="Edit", owner=owner)

@bp.route("/owners/<int:owner_id>/delete", methods=["POST"])
def owners_delete(owner_id):
    if not require_branch_login():
        return redirect(url_for("auth.login"))
    conn, _ = get_branch_conn_from_session()
    cur = conn.cursor()
    cur.execute("DELETE FROM Property_Owner WHERE owner_id=%s", (owner_id,))
    conn.commit()
    cur.close()
    conn.close()
    flash("Owner deleted.", "success")
    return redirect(url_for("branch.owners_list"))

# ================= CUSTOMERS =================

@bp.route("/customers")
def customers_list():
    if not require_branch_login():
        return redirect(url_for("auth.login"))
    conn, branch_key = get_branch_conn_from_session()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM Customer")
    customers = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("customers_list.html", customers=customers, branch_key=branch_key)

@bp.route("/customers/add", methods=["GET", "POST"])
def customers_add():
    if not require_branch_login():
        return redirect(url_for("auth.login"))
    if request.method == "POST":
        first_name = request.form["first_name"]
        middle_name = request.form.get("middle_name", "")
        last_name = request.form["last_name"]
        contact_number = request.form["contact_number"]
        email_address = request.form["email_address"]
        barangay = request.form["barangay"]

        conn, _ = get_branch_conn_from_session()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Customer (
                first_name, middle_name, last_name, contact_number,
                email_address, barangay, password_hash, date_registered
            ) VALUES (%s,%s,%s,%s,%s,%s,'default', NOW())
        """, (first_name, middle_name, last_name, contact_number, email_address, barangay))
        conn.commit()
        cur.close()
        conn.close()
        flash("Customer added.", "success")
        return redirect(url_for("branch.customers_list"))

    return render_template("customers_form.html", action="Add", customer=None)

@bp.route("/customers/<int:customer_id>/edit", methods=["GET", "POST"])
def customers_edit(customer_id):
    if not require_branch_login():
        return redirect(url_for("auth.login"))
    conn, _ = get_branch_conn_from_session()
    cur = conn.cursor(dictionary=True)

    if request.method == "POST":
        first_name = request.form["first_name"]
        middle_name = request.form.get("middle_name", "")
        last_name = request.form["last_name"]
        contact_number = request.form["contact_number"]
        email_address = request.form["email_address"]
        barangay = request.form["barangay"]

        cur.execute("""
            UPDATE Customer
            SET first_name=%s, middle_name=%s, last_name=%s,
                contact_number=%s, email_address=%s, barangay=%s
            WHERE customer_id=%s
        """, (first_name, middle_name, last_name, contact_number, email_address, barangay, customer_id))
        conn.commit()
        cur.close()
        conn.close()
        flash("Customer updated.", "success")
        return redirect(url_for("branch.customers_list"))

    cur.execute("SELECT * FROM Customer WHERE customer_id=%s", (customer_id,))
    customer = cur.fetchone()
    cur.close()
    conn.close()
    if not customer:
        flash("Customer not found.", "error")
        return redirect(url_for("branch.customers_list"))
    return render_template("customers_form.html", action="Edit", customer=customer)

@bp.route("/customers/<int:customer_id>/delete", methods=["POST"])
def customers_delete(customer_id):
    if not require_branch_login():
        return redirect(url_for("auth.login"))
    conn, _ = get_branch_conn_from_session()
    cur = conn.cursor()
    cur.execute("DELETE FROM Customer WHERE customer_id=%s", (customer_id,))
    conn.commit()
    cur.close()
    conn.close()
    flash("Customer deleted.", "success")
    return redirect(url_for("branch.customers_list"))

# ================= APPOINTMENTS =================

@bp.route("/appointments")
def appointments_list():
    if not require_branch_login():
        return redirect(url_for("auth.login"))
    conn, branch_key = get_branch_conn_from_session()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT a.appointment_id, p.title AS property_title,
               c.first_name AS customer_name,
               a.appointment_datetime, a.status
        FROM Appointment a
        JOIN Property p ON a.property_id = p.property_id
        JOIN Customer c ON a.customer_id = c.customer_id
    """)
    appointments = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("appointments_list.html", appointments=appointments, branch_key=branch_key)

@bp.route("/appointments/add", methods=["GET", "POST"])
def appointments_add():
    if not require_branch_login():
        return redirect(url_for("auth.login"))
    conn, _ = get_branch_conn_from_session()
    cur = conn.cursor(dictionary=True)

    # Load properties & customers for dropdowns
    cur.execute("SELECT property_id, title FROM Property")
    properties = cur.fetchall()
    cur.execute("SELECT customer_id, first_name, last_name FROM Customer")
    customers = cur.fetchall()

    if request.method == "POST":
        property_id = request.form["property_id"]
        customer_id = request.form["customer_id"]
        appointment_datetime = request.form["appointment_datetime"]
        status = request.form["status"]

        cur2 = conn.cursor()
        cur2.execute("""
            INSERT INTO Appointment (property_id, customer_id, appointment_datetime, status, date_created)
            VALUES (%s,%s,%s,%s,NOW())
        """, (property_id, customer_id, appointment_datetime, status))
        conn.commit()
        cur2.close()
        cur.close()
        conn.close()
        flash("Appointment created.", "success")
        return redirect(url_for("branch.appointments_list"))

    cur.close()
    conn.close()
    return render_template("appointments_form.html", action="Add",
                           properties=properties, customers=customers, appointment=None)

# ================= MESSAGES =================

@bp.route("/messages")
def messages_list():
    if not require_branch_login():
        return redirect(url_for("auth.login"))
    conn, branch_key = get_branch_conn_from_session()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT m.message_id, c.first_name AS customer_name,
               o.first_name AS owner_name,
               m.message_content, m.timestamp,
               m.sender_type, m.receiver_type
        FROM Message_Communication m
        LEFT JOIN Customer c ON m.customer_id = c.customer_id
        LEFT JOIN Property_Owner o ON m.owner_id = o.owner_id
        ORDER BY m.timestamp DESC
    """)
    messages = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("messages_list.html", messages=messages, branch_key=branch_key)

@bp.route("/messages/add", methods=["GET", "POST"])
def messages_add():
    if not require_branch_login():
        return redirect(url_for("auth.login"))
    conn, _ = get_branch_conn_from_session()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT customer_id, first_name, last_name FROM Customer")
    customers = cur.fetchall()
    cur.execute("SELECT owner_id, first_name, last_name FROM Property_Owner")
    owners = cur.fetchall()

    if request.method == "POST":
        customer_id = request.form["customer_id"]
        owner_id = request.form["owner_id"]
        message_content = request.form["message_content"]
        sender_type = request.form["sender_type"]
        receiver_type = "owner" if sender_type == "customer" else "customer"

        cur2 = conn.cursor()
        cur2.execute("""
            INSERT INTO Message_Communication (
                customer_id, owner_id, message_content, timestamp,
                sender_type, receiver_type
            ) VALUES (%s,%s,%s, NOW(), %s,%s)
        """, (customer_id, owner_id, message_content, sender_type, receiver_type))
        conn.commit()
        cur2.close()
        cur.close()
        conn.close()
        flash("Message added.", "success")
        return redirect(url_for("branch.messages_list"))

    cur.close()
    conn.close()
    return render_template("messages_form.html", customers=customers, owners=owners)
