from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "student_management_secret_key"


def get_connection():
    return sqlite3.connect("students.db")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_connection()
        cur = conn.cursor()

        try:
            cur.execute(
                "INSERT INTO users(username,password) VALUES(?,?)",
                (username, password)
            )

            conn.commit()
            conn.close()

            return redirect("/login")

        except:

            conn.close()

            return "Username already exists!"

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )

        user = cur.fetchone()

        conn.close()

        if user:

            session["user_id"] = user[0]
            session["username"] = user[1]

            return redirect("/")

        return "Invalid Username or Password!"

    return render_template("login.html")


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")
@app.route("/", methods=["GET", "POST"])
def home():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":

        name = request.form["name"]
        rollno = request.form["rollno"]
        course = request.form["course"]

        cur.execute(
            "INSERT INTO students(user_id, name, rollno, course) VALUES(?,?,?,?)",
            (
                session["user_id"],
                name,
                rollno,
                course
            )
        )

        conn.commit()

    search = request.args.get("search")

    if search:

        cur.execute(
            """
            SELECT * FROM students
            WHERE user_id=?
            AND (name LIKE ? OR rollno LIKE ?)
            """,
            (
                session["user_id"],
                "%" + search + "%",
                "%" + search + "%"
            )
        )

    else:

        cur.execute(
            "SELECT * FROM students WHERE user_id=?",
            (session["user_id"],)
        )

    students = cur.fetchall()

    conn.close()

    return render_template(
        "index.html",
        students=students,
        username=session["username"]
    )
# Delete Student
@app.route("/delete/<int:id>")
def delete(id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM students WHERE id=? AND user_id=?",
        (id, session["user_id"])
    )

    conn.commit()
    conn.close()

    return redirect("/")


# Edit Student
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":

        name = request.form["name"]
        rollno = request.form["rollno"]
        course = request.form["course"]

        cur.execute(
            """
            UPDATE students
            SET name=?, rollno=?, course=?
            WHERE id=? AND user_id=?
            """,
            (name, rollno, course, id, session["user_id"])
        )

        conn.commit()
        conn.close()

        return redirect("/")

    cur.execute(
        "SELECT * FROM students WHERE id=? AND user_id=?",
        (id, session["user_id"])
    )

    student = cur.fetchone()

    conn.close()

    return render_template("edit.html", student=student)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)