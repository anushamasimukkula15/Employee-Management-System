from flask import Flask, request, redirect, render_template, session
import sqlite3

app = Flask(__name__, template_folder="Templates")
app.secret_key = "mysecretkey"


# --------------------------------
# Database Connection
# --------------------------------

def get_database_connection():
    connection = sqlite3.connect("users_v3.db")
    connection.row_factory = sqlite3.Row
    return connection


# --------------------------------
# Create Database and Tables
# --------------------------------

def create_database():

    connection = get_database_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
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
            salary INTEGER NOT NULL,
            Joining_Date TEXT NOT NULL,
            address TEXT
        )
    """)

    connection.commit()
    connection.close()


create_database()


# --------------------------------
# Theme Function
# --------------------------------

def get_theme():
    return session.get("theme", "light")


@app.route("/set-theme/<theme>")
def set_theme(theme):

    if theme in ["light", "dark"]:
        session["theme"] = theme

    return redirect(request.referrer or "/")


# --------------------------------
# Home Page
# --------------------------------

@app.route("/")
@app.route("/home")
def home():

    return render_template(
        "home.html",
        theme=get_theme()
    )


# --------------------------------
# Employees Page
# --------------------------------

@app.route("/employees")
def employees():

    connection = get_database_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM employees
        ORDER BY id ASC
    """)

    employees = cursor.fetchall()
    connection.close()

    return render_template(
        "employees.html",
        employees=employees,
        theme=get_theme()
    )


# --------------------------------
# Add Employee
# --------------------------------

@app.route("/add-employee", methods=["GET", "POST"])
def add_employee():

    if request.method == "POST":

        name = request.form["employeename"]
        email = request.form["email"]
        phone_number = request.form["phone_number"]
        department = request.form["department"]
        salary = request.form["salary"]
        joining_date = request.form["Joining_Date"]
        address = request.form["address"]

        connection = get_database_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO employees
            (
                employeename,
                email,
                phone_number,
                department,
                salary,
                Joining_Date,
                address
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            email,
            phone_number,
            department,
            salary,
            joining_date,
            address
        ))

        connection.commit()
        connection.close()

        return redirect("/employees")

    return render_template(
        "add-employee.html",
        theme=get_theme()
    )


# --------------------------------
# Search Employee
# --------------------------------

@app.route("/search", methods=["GET", "POST"])
def search():

    results = []

    if request.method == "POST":

        keyword = request.form["keyword"]

        connection = get_database_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT * FROM employees
            WHERE employeename LIKE ?
            OR email LIKE ?
            OR department LIKE ?
        """, (
            "%" + keyword + "%",
            "%" + keyword + "%",
            "%" + keyword + "%"
        ))

        results = cursor.fetchall()
        connection.close()

    return render_template(
        "search.html",
        results=results,
        theme=get_theme()
    )


# --------------------------------
# Register
# --------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        fullname = request.form["fullname"]
        username = request.form["username"]
        password = request.form["password"]

        connection = get_database_connection()
        cursor = connection.cursor()

        try:

            cursor.execute("""
                INSERT INTO users
                (fullname, username, password)
                VALUES (?, ?, ?)
            """, (
                fullname,
                username,
                password
            ))

            connection.commit()
            connection.close()

            return redirect("/login")

        except sqlite3.IntegrityError:

            connection.close()

            return """
                <h2>Username already exists!</h2>
                <a href="/register">Try Again</a>
            """

    return render_template(
        "register.html",
        theme=get_theme()
    )


# --------------------------------
# Login
# --------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        connection = get_database_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT * FROM users
            WHERE username = ? AND password = ?
        """, (
            username,
            password
        ))

        user = cursor.fetchone()
        connection.close()

        if user:

            return redirect("/")

        else:

            return """
                <h2>Login Failed!</h2>
                <p>Username or password is incorrect.</p>
                <a href="/login">Try Again</a>
            """

    return render_template(
        "login.html",
        theme=get_theme()
    )


# --------------------------------
# Edit Employee
# --------------------------------

@app.route("/edit-employee/<int:id>", methods=["GET", "POST"])
def edit_employee(id):

    connection = get_database_connection()
    cursor = connection.cursor()

    if request.method == "GET":

        cursor.execute("""
            SELECT * FROM employees
            WHERE id = ?
        """, (id,))

        employee = cursor.fetchone()
        connection.close()

        if employee is None:
            return "Employee not found", 404

        return render_template(
            "edit-employee.html",
            employee=employee,
            theme=get_theme()
        )

    name = request.form["employeename"]
    email = request.form["email"]
    phone_number = request.form["phone_number"]
    department = request.form["department"]
    salary = request.form["salary"]
    joining_date = request.form["Joining_Date"]
    address = request.form["address"]

    cursor.execute("""
        UPDATE employees
        SET
            employeename = ?,
            email = ?,
            phone_number = ?,
            department = ?,
            salary = ?,
            Joining_Date = ?,
            address = ?
        WHERE id = ?
    """, (
        name,
        email,
        phone_number,
        department,
        salary,
        joining_date,
        address,
        id
    ))

    connection.commit()
    connection.close()

    return redirect("/employees")


# --------------------------------
# Delete Employee
# --------------------------------

@app.route("/delete-employee/<int:id>", methods=["POST"])
def delete_employee(id):

    connection = get_database_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM employees
        WHERE id = ?
    """, (id,))

    connection.commit()
    connection.close()

    return redirect("/employees")


# --------------------------------
# Run Application
# --------------------------------

if __name__ == "__main__":
    app.run(debug=True)