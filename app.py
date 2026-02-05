from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

app = Flask(__name__)
app.secret_key = "college_secret"

# ---------- TOKEN SERIALIZER ----------
s = URLSafeTimedSerializer(app.secret_key)

# ---------- DATABASE ----------
def get_db():
    conn = sqlite3.connect("colleges.db")
    conn.row_factory = sqlite3.Row
    return conn

#------------- HOME ----------------------
@app.route("/")
def home():
    return render_template("home.html")

# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cur.fetchone()
        db.close()

        if user and check_password_hash(user["password"], password):
            session["user"] = username
            session["role"] = user["role"] if "role" in user.keys() else "student"
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password", "error")

    return render_template("login.html")

# ---------- REGISTER ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        fname = request.form["fname"]
        lname = request.form["lname"]
        email = request.form["email"]
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        db = get_db()
        cur = db.cursor()
        cur.execute("""
            INSERT INTO users (fname, lname, email, username, password)
            VALUES (?,?,?,?,?)
        """, (fname, lname, email, username, password))
        db.commit()
        db.close()

        flash("Registration successful! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM student")
    students = cur.fetchall()
    db.close()

    return render_template("dashboard.html", students=students)

# ---------- ADD STUDENT ----------
@app.route("/add_student", methods=["GET", "POST"])
def add_student():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        sname = request.form["sname"]
        sbranch = request.form["sbranch"]
        smarks = request.form["smarks"]
        phno = request.form["phno"]

        db = get_db()
        cur = db.cursor()
        cur.execute("""
            INSERT INTO student (sname, sbranch, smarks, phno)
            VALUES (?,?,?,?)
        """, (sname, sbranch, smarks, phno))
        db.commit()
        db.close()

        flash("Student added successfully", "success")
        return redirect(url_for("dashboard"))

    return render_template("add_student.html")

# ---------- EDIT STUDENT ----------
@app.route("/edit/<int:sid>", methods=["GET", "POST"])
def edit_student(sid):
    if "user" not in session:
        return redirect(url_for("login"))

    db = get_db()
    cur = db.cursor()

    if request.method == "POST":
        smarks = request.form["smarks"]
        cur.execute("UPDATE student SET smarks=? WHERE sid=?", (smarks, sid))
        db.commit()
        db.close()
        return redirect(url_for("dashboard"))

    cur.execute("SELECT * FROM student WHERE sid=?", (sid,))
    student = cur.fetchone()
    db.close()

    return render_template("edit_student.html", student=student)

# ---------- DELETE STUDENT ----------
@app.route("/delete/<int:sid>")
def delete_student(sid):
    if "user" not in session:
        return redirect(url_for("login"))

    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM student WHERE sid=?", (sid,))
    db.commit()
    db.close()

    flash("Student deleted", "warning")
    return redirect(url_for("dashboard"))

# ---------- ABOUT ----------
@app.route("/about")
def about():
    return render_template("about.html")

# ---------- EMAIL CONFIG ----------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'likhitharavi03@gmail.com'
app.config['MAIL_PASSWORD'] = 'neokkawglsggkoey'
app.config['MAIL_DEFAULT_SENDER'] = 'likhitharavi03@gmail.com'

mail = Mail(app)

# ---------- CONTACT ----------
@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        message = request.form["message"]

        msg = Message(
            subject="New Contact Message - SMS",
            recipients=["likhitharavi03@gmail.com"],
            body=f"""
Student Management System - Contact Message

Name   : {name}
Email  : {email}
Message:{message}
"""
        )

        try:
            mail.send(msg)
            flash("Email successfully sent!", "success")
        except Exception as e:
            flash("Failed to send email.", "error")
            print(e)

        return redirect(url_for("contact"))

    return render_template("contact.html")

# ---------- FORGOT PASSWORD ----------
@app.route("/forgot")
def forgot():
    return render_template("forgot_password.html")

@app.route("/send_reset_link", methods=["POST"])
def send_reset_link():
    email = request.form["email"]

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM users WHERE email=?", (email,))
    user = cur.fetchone()
    db.close()

    if not user:
        flash("Email not registered!", "error")
        return redirect(url_for("forgot"))

    token = s.dumps(email, salt="password-reset-salt")
    reset_link = url_for("reset_password", token=token, _external=True)

    msg = Message(
        subject="Password Reset Request",
        recipients=[email],
        body=f"""
Hello {user['fname']},

Click the link below to reset your password:
{reset_link}

This link is valid for 5 minutes.
"""
    )

    mail.send(msg)
    flash("Reset link sent to your email!", "success")
    return redirect(url_for("login"))

@app.route("/reset/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        email = s.loads(token, salt="password-reset-salt", max_age=300)
    except SignatureExpired:
        return "Reset link expired!"
    except BadSignature:
        return "Invalid reset link!"

    if request.method == "POST":
        new_password = generate_password_hash(request.form["password"])

        db = get_db()
        cur = db.cursor()
        cur.execute("UPDATE users SET password=? WHERE email=?", (new_password, email))
        db.commit()
        db.close()

        flash("Password reset successful! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("reset_password.html")

# ---------- SEARCH STUDENT ----------
@app.route("/search", methods=["GET", "POST"])
def search():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form["name"]

        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM student WHERE sname LIKE ?", (f"%{name}%",))
        students = cur.fetchall()
        db.close()

        return render_template("result.html", students=students)

    return render_template("search.html")

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)
