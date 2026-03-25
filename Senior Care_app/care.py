from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from functools import wraps
from datetime import date
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
    # Create tables if they do not exist yet.
    # This app stores everything in a local SQLite database.
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
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS medications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resident_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            dosage TEXT,
            -- Save time is used only for ordering in the UI.
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (resident_id) REFERENCES residents (id) ON DELETE CASCADE
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS medication_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medication_id INTEGER NOT NULL,
            given_date TEXT NOT NULL,
            given_by TEXT,
            -- We save when staff checked the medication.
            given_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (medication_id) REFERENCES medications (id) ON DELETE CASCADE,
            -- One row per medication per day.
            UNIQUE (medication_id, given_date)
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
    # Used for the "today" medication checklist.
    today = date.today().isoformat()
    db = get_db_connection()
    if q:
        residents = db.execute(
            "SELECT * FROM residents WHERE name LIKE ? ORDER BY name",
            (f"%{q}%",),
        ).fetchall()
    else:
        residents = db.execute("SELECT * FROM residents ORDER BY name").fetchall()

    # Find residents with BP > 140 (high alert).
    # This is a simple loop so staff can see urgency fast.
    high_alert_names = []
    for resident in residents:
        if resident["bp"] > 140:
            high_alert_names.append(resident["name"])

    medications_by_resident = {}
    given_ids_by_resident = {}
    resident_ids = [resident["id"] for resident in residents]

    if resident_ids:
        # Build a SQL IN clause like "?, ?, ?" for N residents.
        placeholders = ",".join(["?"] * len(resident_ids))

        # Load medications for all residents on the dashboard.
        medications = db.execute(
            f"""
            SELECT id, resident_id, name, dosage, created_at
            FROM medications
            WHERE resident_id IN ({placeholders})
            ORDER BY created_at DESC
            """,
            resident_ids,
        ).fetchall()

        # Group medications by resident id.
        for med in medications:
            rid = med["resident_id"]
            if rid not in medications_by_resident:
                medications_by_resident[rid] = []
            medications_by_resident[rid].append(med)

        # Load medication checks for today.
        # We join logs -> medications to get resident_id.
        given_rows = db.execute(
            f"""
            SELECT ml.medication_id, m.resident_id
            FROM medication_logs ml
            INNER JOIN medications m ON m.id = ml.medication_id
            WHERE m.resident_id IN ({placeholders}) AND ml.given_date = ?
            """,
            (*resident_ids, today),
        ).fetchall()

        for row in given_rows:
            rid = row["resident_id"]
            if rid not in given_ids_by_resident:
                # Keep set for fast "id in given_ids" checks.
                given_ids_by_resident[rid] = set()
            given_ids_by_resident[rid].add(row["medication_id"])

    db.close()
    return render_template(
        "index.html",
        residents=residents,
        high_alert_names=high_alert_names,
        medications_by_resident=medications_by_resident,
        given_ids_by_resident=given_ids_by_resident,
        username=session.get("username"),
        q=q,
        today=today,
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


@app.route("/residents/<int:resident_id>/medications/check", methods=["POST"])
@login_required
def update_medication_checklist(resident_id):
    today = date.today().isoformat()
    # The dashboard sends only the checked medication ids.
    given_ids_raw = request.form.getlist("given_ids")
    given_ids = set()
    for x in given_ids_raw:
        try:
            given_ids.add(int(x))
        except ValueError:
            continue

    db = get_db_connection()
    resident = db.execute(
        "SELECT id FROM residents WHERE id = ?", (resident_id,)
    ).fetchone()
    if not resident:
        db.close()
        flash("Patient not found.", "error")
        return redirect(url_for("home"))

    # We use "today" checkboxes as the source of truth.
    # So we delete today's logs, then re-add the checked ones.
    db.execute(
        """
        DELETE FROM medication_logs
        WHERE medication_id IN (
            SELECT id FROM medications WHERE resident_id = ?
        )
        AND given_date = ?
        """,
        (resident_id, today),
    )

    if given_ids:
        rows = [(mid, today, session.get("username")) for mid in given_ids]
        db.executemany(
            """
            INSERT INTO medication_logs (medication_id, given_date, given_by)
            VALUES (?, ?, ?)
            """,
            rows,
        )

    db.commit()
    db.close()
    flash("Medication checklist saved.", "success")
    return redirect(url_for("home"))


@app.route("/residents/<int:resident_id>", methods=["GET", "POST"])
@login_required
def resident_detail(resident_id):
    # Old page (notes + meds together).
    # We redirect to the new Notes-only page.
    return redirect(url_for("resident_notes", resident_id=resident_id))


@app.route("/residents/<int:resident_id>/notes", methods=["GET", "POST"])
@login_required
def resident_notes(resident_id):
    # Notes-only page.
    db = get_db_connection()
    resident = db.execute(
        "SELECT * FROM residents WHERE id = ?", (resident_id,)
    ).fetchone()

    if not resident:
        db.close()
        flash("Patient not found.", "error")
        return redirect(url_for("home"))

    if request.method == "POST":
        # Save a new note.
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
        "notes_page.html",
        resident=resident,
        notes=notes,
        username=session.get("username"),
    )


@app.route("/residents/<int:resident_id>/medications", methods=["GET", "POST"])
@login_required
def resident_medications(resident_id):
    # Medications-only page.
    db = get_db_connection()
    resident = db.execute(
        "SELECT * FROM residents WHERE id = ?", (resident_id,)
    ).fetchone()

    if not resident:
        db.close()
        flash("Patient not found.", "error")
        return redirect(url_for("home"))

    today = date.today().isoformat()

    if request.method == "POST":
        action = request.form.get("action", "")

        if action == "add":
            # Add a new medication.
            med_name = request.form.get("med_name", "").strip()
            med_dosage = request.form.get("med_dosage", "").strip()
            if not med_name:
                flash("Medication name is required.", "error")
            else:
                db.execute(
                    "INSERT INTO medications (resident_id, name, dosage) VALUES (?, ?, ?)",
                    (resident_id, med_name, med_dosage or None),
                )
                db.commit()
                flash("Medication added.", "success")

        elif action == "checklist":
            # Save today's checklist.
            given_ids_raw = request.form.getlist("given_ids")
            given_ids = set()
            for x in given_ids_raw:
                try:
                    given_ids.add(int(x))
                except ValueError:
                    continue

            db.execute(
                """
                DELETE FROM medication_logs
                WHERE medication_id IN (
                    SELECT id FROM medications WHERE resident_id = ?
                )
                AND given_date = ?
                """,
                (resident_id, today),
            )

            if given_ids:
                rows = [(mid, today, session.get("username")) for mid in given_ids]
                db.executemany(
                    """
                    INSERT INTO medication_logs (medication_id, given_date, given_by)
                    VALUES (?, ?, ?)
                    """,
                    rows,
                )
            db.commit()
            flash("Medication checklist saved.", "success")

    medications = db.execute(
        "SELECT id, name, dosage FROM medications WHERE resident_id = ? ORDER BY created_at DESC",
        (resident_id,),
    ).fetchall()

    given_medication_ids = set()
    if medications:
        given_rows = db.execute(
            """
            SELECT ml.medication_id
            FROM medication_logs ml
            INNER JOIN medications m ON m.id = ml.medication_id
            WHERE m.resident_id = ? AND ml.given_date = ?
            """,
            (resident_id, today),
        ).fetchall()
        given_medication_ids = {row["medication_id"] for row in given_rows}

    db.close()

    return render_template(
        "medications_page.html",
        resident=resident,
        medications=medications,
        given_medication_ids=given_medication_ids,
        today=today,
        username=session.get("username"),
    )


@app.route(
    "/residents/<int:resident_id>/medications/<int:medication_id>/delete",
    methods=["POST"],
)
@login_required
def delete_medication(resident_id, medication_id):
    # Remove one medication from a resident.
    db = get_db_connection()

    med = db.execute(
        "SELECT id, resident_id FROM medications WHERE id = ?",
        (medication_id,),
    ).fetchone()

    if not med:
        db.close()
        abort(404)

    # Safety: do not delete meds from another resident.
    if med["resident_id"] != resident_id:
        db.close()
        abort(404)

    db.execute("DELETE FROM medications WHERE id = ?", (medication_id,))
    db.commit()
    db.close()

    flash("Medication removed.", "success")
    return redirect(url_for("resident_medications", resident_id=resident_id))


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


@app.route("/residents/<int:resident_id>/doctor-summary", methods=["GET"])
@login_required
def doctor_summary(resident_id):
    """
    Read-only "Report" page.
    A doctor can review a patient fast on one screen.
    """
    # Open the database.
    db = get_db_connection()

    # Get the resident info.
    resident = db.execute(
        "SELECT * FROM residents WHERE id = ?", (resident_id,)
    ).fetchone()

    if not resident:
        # Stop if the resident does not exist.
        db.close()
        flash("Patient not found.", "error")
        return redirect(url_for("home"))

    # Use ISO date like 2026-03-25.
    today = date.today().isoformat()

    # Load BP history (newest first).
    readings = db.execute(
        "SELECT bp, recorded_at FROM bp_readings WHERE resident_id = ? ORDER BY recorded_at DESC",
        (resident_id,),
    ).fetchall()

    # Load notes (newest first).
    notes = db.execute(
        "SELECT content, author, created_at FROM notes WHERE resident_id = ? ORDER BY created_at DESC",
        (resident_id,),
    ).fetchall()

    # Load medication list for this resident.
    medications = db.execute(
        "SELECT id, name, dosage FROM medications WHERE resident_id = ? ORDER BY created_at DESC",
        (resident_id,),
    ).fetchall()

    # Track which meds were given today.
    given_medication_ids = set()
    if medications:
        # Join logs with meds to filter by resident.
        given_rows = db.execute(
            """
            SELECT ml.medication_id
            FROM medication_logs ml
            INNER JOIN medications m ON m.id = ml.medication_id
            WHERE m.resident_id = ? AND ml.given_date = ?
            """,
            (resident_id, today),
        ).fetchall()
        given_medication_ids = {row["medication_id"] for row in given_rows}

    # Close the database.
    db.close()

    # Render the "Report" page.
    return render_template(
        "doctor_summary.html",
        resident=resident,
        readings=readings,
        notes=notes,
        medications=medications,
        given_medication_ids=given_medication_ids,
        today=today,
        username=session.get("username"),
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True)