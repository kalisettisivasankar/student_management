from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "student_management_secret_key"

# Folder path to save uploaded student photos on Render
UPLOAD_FOLDER = '/tmp/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create the uploads directory if it does not exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

DB_PATH = os.path.join('/tmp', 'students.db')

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)
    
    # Added PHONE, EMAIL, and PHOTO columns to the students table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        rollno TEXT,
        course TEXT,
        phone TEXT,
        email TEXT,
        photo TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    conn.commit()
    conn.close()

# Called outside so Gunicorn executes it and creates tables automatically
init_db()


# Route to serve and display uploaded student photos in the browser
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users(username,password) VALUES(?,?)", (username, password))
            conn.commit()
            conn.close()
            return redirect("/login")
        except Exception as e:
            conn.close()
            return f"Registration failed! Error: {str(e)}"
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
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
        phone = request.form["phone"]
        email = request.form["email"]
        
        # Handling file upload logic for student photo
        file = request.files.get("photo")
        filename = ""
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        cur.execute(
            "INSERT INTO students(user_id, name, rollno, course, phone, email, photo) VALUES(?,?,?,?,?,?,?)",
            (session["user_id"], name, rollno, course, phone, email, filename)
        )
        conn.commit()

    search = request.args.get("search")
    if search:
        cur.execute(
            "SELECT * FROM students WHERE user_id=? AND (name LIKE ? OR rollno LIKE ?)",
            (session["user_id"], "%" + search + "%", "%" + search + "%")
        )
    else:
        cur.execute("SELECT * FROM students WHERE user_id=?", (session["user_id"],))

    students = cur.fetchall()
    conn.close()
    return render_template("index.html", students=students, username=session["username"])


@app.route("/delete/<int:id>")
def delete(id):
    if "user_id" not in session:
        return redirect("/login")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM students WHERE id=? AND user_id=?", (id, session["user_id"]))
    conn.commit()
    conn.close()
    return redirect("/")


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
        phone = request.form["phone"]
        email = request.form["email"]
        
        file = request.files.get("photo")
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            cur.execute(
                "UPDATE students SET name=?, rollno=?, course=?, phone=?, email=?, photo=? WHERE id=? AND user_id=?",
                (name, rollno, course, phone, email, filename, id, session["user_id"])
            )
        else:
            cur.execute(
                "UPDATE students SET name=?, rollno=?, course=?, phone=?, email=? WHERE id=? AND user_id=?",
                (name, rollno, course, phone, email, id, session["user_id"])
            )
        conn.commit()
        conn.close()
        return redirect("/")

    cur.execute("SELECT * FROM students WHERE id=? AND user_id=?", (id, session["user_id"]))
    student = cur.fetchone()
    conn.close()
    return render_template("edit.html", student=student)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
