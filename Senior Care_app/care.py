from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = "change-this-secret"


def get_db_connection():
    conn = sqlite3.connect("Seniorcare.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS residents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            bp INTEGER NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resident_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            author TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (resident_id) REFERENCES residents (id) ON DELETE CASCADE
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS bp_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resident_id INTEGER NOT NULL,
            bp INTEGER NOT NULL,
            recorded_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (resident_id) REFERENCES residents (id) ON DELETE CASCADE
        )
        """
    )
    conn.commit()
    conn.close()


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(**kwargs)

    return wrapped_view


@app.route("/")
@login_required
def home():
    q = request.args.get("q", "").strip()
    db = get_db_connection()
    if q:
        residents = db.execute(
            "SELECT * FROM residents WHERE name LIKE ? ORDER BY name",
            (f"%{q}%",),
        ).fetchall()
    else:
        residents = db.execute("SELECT * FROM residents ORDER BY name").fetchall()
    db.close()
    return render_template(
        "index.html",
        residents=residents,
        username=session.get("username"),
        q=q,
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password are required.", "error")
            return render_template("register.html")

        db = get_db_connection()
        try:
            db.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, generate_password_hash(password)),
            )
            db.commit()
        except sqlite3.IntegrityError:
            flash("Username already exists. Please choose another.", "error")
            return render_template("register.html")
        finally:
            db.close()

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        db = get_db_connection()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        db.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash("Logged in successfully.", "success")
            return redirect(url_for("home"))

        flash("Invalid username or password.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app.route("/residents/new", methods=["GET", "POST"])
@login_required
def new_resident():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        age_raw = request.form.get("age", "").strip()
        bp_raw = request.form.get("bp", "").strip()

        if not name:
            flash("Name is required.", "error")
            return render_template("new_resident.html", username=session.get("username"))

        try:
            age = int(age_raw)
            bp = int(bp_raw)
        except ValueError:
            flash("Age and BP must be numbers.", "error")
            return render_template("new_resident.html", username=session.get("username"))

        if age <= 0 or age > 130:
            flash("Please enter a valid age.", "error")
            return render_template("new_resident.html", username=session.get("username"))

        if bp <= 0 or bp > 400:
            flash("Please enter a valid BP.", "error")
            return render_template("new_resident.html", username=session.get("username"))

        db = get_db_connection()
        db.execute(
            "INSERT INTO residents (name, age, bp) VALUES (?, ?, ?)",
            (name, age, bp),
        )
        db.commit()
        db.close()

        flash("Patient added.", "success")
        return redirect(url_for("home"))

    return render_template("new_resident.html", username=session.get("username"))


@app.route("/residents/<int:resident_id>/edit", methods=["GET", "POST"])
@login_required
def edit_resident(resident_id):
    db = get_db_connection()
    resident = db.execute(
        "SELECT * FROM residents WHERE id = ?", (resident_id,)
    ).fetchone()

    if not resident:
        db.close()
        flash("Patient not found.", "error")
        return redirect(url_for("home"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        age_raw = request.form.get("age", "").strip()
        bp_raw = request.form.get("bp", "").strip()

        if not name:
            flash("Name is required.", "error")
            db.close()
            return redirect(url_for("edit_resident", resident_id=resident_id))

        try:
            age = int(age_raw)
            bp = int(bp_raw)
        except ValueError:
            flash("Age and BP must be numbers.", "error")
            db.close()
            return redirect(url_for("edit_resident", resident_id=resident_id))

        if age <= 0 or age > 130:
            flash("Please enter a valid age.", "error")
            db.close()
            return redirect(url_for("edit_resident", resident_id=resident_id))

        if bp <= 0 or bp > 400:
            flash("Please enter a valid BP.", "error")
            db.close()
            return redirect(url_for("edit_resident", resident_id=resident_id))

        db.execute(
            "UPDATE residents SET name = ?, age = ?, bp = ? WHERE id = ?",
            (name, age, bp, resident_id),
        )
        db.commit()
        db.close()

        flash("Patient information updated.", "success")
        return redirect(url_for("resident_detail", resident_id=resident_id))

    db.close()
    return render_template(
        "edit_resident.html",
        resident=resident,
        username=session.get("username"),
    )


@app.route("/residents/<int:resident_id>/delete", methods=["POST"])
@login_required
def delete_resident(resident_id):
    db = get_db_connection()
    resident = db.execute(
        "SELECT * FROM residents WHERE id = ?", (resident_id,)
    ).fetchone()

    if not resident:
        db.close()
        flash("Patient not found.", "error")
        return redirect(url_for("home"))

    db.execute("DELETE FROM residents WHERE id = ?", (resident_id,))
    db.commit()
    db.close()

    flash("Patient deleted.", "success")
    return redirect(url_for("home"))


@app.route("/residents/<int:resident_id>", methods=["GET", "POST"])
@login_required
def resident_detail(resident_id):
    db = get_db_connection()
    resident = db.execute(
        "SELECT * FROM residents WHERE id = ?", (resident_id,)
    ).fetchone()

    if not resident:
        db.close()
        flash("Patient not found.", "error")
        return redirect(url_for("home"))

    if request.method == "POST":
        content = request.form.get("content", "").strip()
        if not content:
            flash("Note cannot be empty.", "error")
        else:
            db.execute(
                "INSERT INTO notes (resident_id, content, author) VALUES (?, ?, ?)",
                (resident_id, content, session.get("username")),
            )
            db.commit()
            flash("Note added.", "success")

    notes = db.execute(
        "SELECT content, author, created_at FROM notes WHERE resident_id = ? ORDER BY created_at DESC",
        (resident_id,),
    ).fetchall()
    db.close()

    return render_template(
        "resident_detail.html",
        resident=resident,
        notes=notes,
        username=session.get("username"),
    )


@app.route("/residents/<int:resident_id>/bp", methods=["GET", "POST"])
@login_required
def bp_history(resident_id):
    db = get_db_connection()
    resident = db.execute(
        "SELECT * FROM residents WHERE id = ?", (resident_id,)
    ).fetchone()

    if not resident:
        db.close()
        flash("Patient not found.", "error")
        return redirect(url_for("home"))

    if request.method == "POST":
        bp_raw = request.form.get("bp", "").strip()
        if not bp_raw:
            flash("Blood pressure value is required.", "error")
        else:
            try:
                bp = int(bp_raw)
            except ValueError:
                flash("Blood pressure must be a number.", "error")
            else:
                if bp <= 0 or bp > 400:
                    flash("Please enter a valid blood pressure.", "error")
                else:
                    db.execute(
                        "INSERT INTO bp_readings (resident_id, bp) VALUES (?, ?)",
                        (resident_id, bp),
                    )
                    db.commit()
                    flash("Blood pressure reading added.", "success")

    readings = db.execute(
        "SELECT bp, recorded_at FROM bp_readings WHERE resident_id = ? ORDER BY recorded_at DESC",
        (resident_id,),
    ).fetchall()
    db.close()

    return render_template(
        "bp_history.html",
        resident=resident,
        readings=readings,
        username=session.get("username"),
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True)