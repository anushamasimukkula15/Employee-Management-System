from flask import (
    Flask, render_template, request, redirect,
    url_for, session, make_response
)
import sqlite3
from functools import wraps
from datetime import timedelta
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, template_folder="Templates")
app.secret_key = "mysecretkey"
app.permanent_session_lifetime = timedelta(days=30)

DATABASE = "users_v3.db"


# ================= DATABASE =================

def get_database_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def create_database():
    connection = get_database_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employeename TEXT NOT NULL,
            email TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            department TEXT NOT NULL,
            salary REAL NOT NULL,
            Joining_Date TEXT NOT NULL,
            address TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


# ================= LOGIN REQUIRED =================

def login_required(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return function(*args, **kwargs)

    return decorated_function


# ================= THEME =================

@app.context_processor
def inject_theme():
    return {
        "theme": request.cookies.get("theme", "light")
    }


@app.route("/set-theme/<theme>")
def set_theme(theme):
    if theme not in ["light", "dark"]:
        theme = "light"

    response = make_response(
        redirect(request.referrer or url_for("home"))
    )

    response.set_cookie(
        "theme",
        theme,
        max_age=60 * 60 * 24 * 365
    )

    return response


# ================= HOME =================

@app.route("/")
@login_required
def home():
    return render_template("home.html")


# ================= REGISTER =================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        fullname = request.form.get("fullname", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not fullname or not email or not password:
            return "Please fill in all required fields."

        if password != confirm_password:
            return "Passwords do not match."

        hashed_password = generate_password_hash(password)

        connection = get_database_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                INSERT INTO users (fullname, email, password)
                VALUES (?, ?, ?)
            """, (fullname, email, hashed_password))

            connection.commit()

        except sqlite3.IntegrityError:
            connection.close()
            return "Email already registered."

        connection.close()
        return redirect(url_for("login"))

    return render_template("register.html")


# ================= LOGIN =================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            return "Email and password are required."

        connection = get_database_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT * FROM users WHERE email = ?
        """, (email,))

        user = cursor.fetchone()
        connection.close()

        if user and check_password_hash(user["password"], password):
            session.permanent = True
            session["user_id"] = user["id"]
            session["fullname"] = user["fullname"]
            session["email"] = user["email"]

            return redirect(url_for("home"))

        return "Invalid email or password."

    return render_template("login.html")


# ================= LOGOUT =================

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ================= DISPLAY EMPLOYEES =================

@app.route("/employees")
@login_required
def employees():
    connection = get_database_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM employees
        ORDER BY id ASC
    """)

    employee_list = cursor.fetchall()
    connection.close()

    return render_template(
        "employees.html",
        employees=employee_list
    )


# ================= ADD EMPLOYEE =================

@app.route("/add-employee", methods=["GET", "POST"])
@login_required
def add_employee():
    if request.method == "POST":
        employeename = request.form.get("employeename", "").strip()
        email = request.form.get("email", "").strip()
        phone_number = request.form.get("phone_number", "").strip()
        department = request.form.get("department", "").strip()
        salary = request.form.get("salary", "").strip()
        Joining_Date = request.form.get("Joining_Date", "").strip()
        address = request.form.get("address", "").strip()

        if not all([
            employeename, email, phone_number, department,
            salary, Joining_Date, address
        ]):
            return "Please fill in all fields."

        try:
            salary_value = float(salary)
        except ValueError:
            return "Please enter a valid salary."

        connection = get_database_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO employees (
                employeename, email, phone_number,
                department, salary, Joining_Date, address
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            employeename, email, phone_number,
            department, salary_value, Joining_Date, address
        ))

        connection.commit()
        connection.close()

        return redirect(url_for("employees"))

    return render_template("add-employee.html")


# ================= EDIT EMPLOYEE =================

@app.route("/edit-employee/<int:employee_id>", methods=["GET", "POST"])
@login_required
def edit_employee(employee_id):
    connection = get_database_connection()
    cursor = connection.cursor()

    if request.method == "POST":
        employeename = request.form.get("employeename", "").strip()
        email = request.form.get("email", "").strip()
        phone_number = request.form.get("phone_number", "").strip()
        department = request.form.get("department", "").strip()
        salary = request.form.get("salary", "").strip()
        Joining_Date = request.form.get("Joining_Date", "").strip()
        address = request.form.get("address", "").strip()

        if not all([
            employeename, email, phone_number, department,
            salary, Joining_Date, address
        ]):
            connection.close()
            return "Please fill in all fields."

        try:
            salary_value = float(salary)
        except ValueError:
            connection.close()
            return "Please enter a valid salary."

        cursor.execute("""
            UPDATE employees
            SET employeename = ?,
                email = ?,
                phone_number = ?,
                department = ?,
                salary = ?,
                Joining_Date = ?,
                address = ?
            WHERE id = ?
        """, (
            employeename, email, phone_number,
            department, salary_value, Joining_Date,
            address, employee_id
        ))

        connection.commit()
        connection.close()

        return redirect(url_for("employees"))

    cursor.execute("""
        SELECT * FROM employees WHERE id = ?
    """, (employee_id,))

    employee = cursor.fetchone()
    connection.close()

    if employee is None:
        return "Employee not found."

    return render_template(
        "edit-employee.html",
        employee=employee
    )


# ================= DELETE EMPLOYEE =================

@app.route("/delete-employee/<int:employee_id>", methods=["POST"])
@login_required
def delete_employee(employee_id):
    connection = get_database_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM employees
        WHERE id = ?
    """, (employee_id,))

    connection.commit()
    connection.close()

    return redirect(url_for("employees"))


# ================= SEARCH EMPLOYEES =================

@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    employees_list = []
    search_query = ""

    if request.method == "POST":
        search_query = request.form.get("search", "").strip()

        connection = get_database_connection()
        cursor = connection.cursor()

        search_value = f"%{search_query}%"

        cursor.execute("""
            SELECT * FROM employees
            WHERE employeename LIKE ?
               OR email LIKE ?
               OR phone_number LIKE ?
               OR department LIKE ?
               OR address LIKE ?
            ORDER BY id ASC
        """, (
            search_value, search_value, search_value,
            search_value, search_value
        ))

        employees_list = cursor.fetchall()
        connection.close()

    return render_template(
        "search.html",
        employees=employees_list,
        search_query=search_query
    )


# ================= RUN APPLICATION =================

if __name__ == "__main__":
    create_database()
    app.run(debug=True)