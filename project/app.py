from datetime import date, datetime, timedelta
import sqlite3

from flask import Flask, flash, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = "gym-membership-secret-key"
DB_NAME = "gym_members.db"
VALID_PLANS = ["Starter", "Silver", "Gold", "Platinum", "Elite"]


def normalize_plan(plan_name):
    if plan_name is None:
        return ""
    plan = plan_name.strip()
    if not plan:
        return ""
    if plan.lower() == "basic":
        return "Starter"
    return plan


def parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def generate_demo_members():
    plan_fee = {
        "Starter": 1200,
        "Silver": 1800,
        "Gold": 2500,
        "Platinum": 4000,
        "Elite": 5500,
    }
    first_names = [
        "Rahul", "Priya", "Amit", "Neha", "Karan", "Riya", "Deepak", "Anjali",
        "Vikas", "Meera", "Harsh", "Pooja", "Siddh", "Divya", "Arjun", "Tanya",
        "Nitin", "Sneha", "Rohit", "Isha", "Yash", "Mitali", "Ashok", "Komal",
        "Vijay", "Kavya", "Nikhil", "Shruti", "Om", "Aisha", "Manav", "Sara",
        "Jay", "Anita", "Rakesh", "Palak", "Sohan", "Jiya", "Dev", "Nisha",
        "Tarun", "Kriti", "Gaurav", "Rekha", "Hitesh", "Mona", "Abhishek", "Pallavi",
        "Saurabh", "Ritika",
    ]
    last_names = [
        "Sharma", "Verma", "Patel", "Singh", "Gupta", "Mehta", "Joshi", "Reddy",
        "Nair", "Kapoor", "Malhotra", "Iyer", "Desai", "Chauhan", "Saxena", "Kulkarni",
        "Mishra", "Sen", "Roy", "Chopra",
    ]
    plans = ["Starter", "Silver", "Gold", "Platinum", "Elite"]
    members = []

    today = date.today()
    for i in range(1, 51):
        first = first_names[(i - 1) % len(first_names)]
        last = last_names[(i * 3) % len(last_names)]
        name = f"{first} {last}"
        phone = f"98{(i * 137) % 100000000:08d}"
        email = f"{first.lower()}{i}@gymmail.com"
        plan = plans[(i - 1) % len(plans)]
        fee = plan_fee[plan]
        joining_date = (today - timedelta(days=(i * 7) % 140 + 10)).isoformat()

        if i <= 10:
            expiry_date = (today + timedelta(days=((i - 1) % 7) + 1)).isoformat()
        else:
            expiry_date = (today + timedelta(days=20 + ((i - 10) * 6) % 80)).isoformat()

        members.append((name, phone, email, plan, fee, joining_date, expiry_date))

    return members


def init_db():
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                plan TEXT NOT NULL,
                fee REAL NOT NULL,
                discount REAL DEFAULT 0,
                joining_date TEXT NOT NULL,
                expiry_date TEXT NOT NULL
            )
            """
        )

        columns = [row[1] for row in conn.execute("PRAGMA table_info(members)").fetchall()]
        if "discount" not in columns:
            conn.execute("ALTER TABLE members ADD COLUMN discount REAL DEFAULT 0")
            conn.execute("UPDATE members SET discount = 0 WHERE discount IS NULL")

        count = conn.execute("SELECT COUNT(*) FROM members").fetchone()[0]
        if count != 50:
            conn.execute("DELETE FROM members")
            members = generate_demo_members()
            conn.executemany(
                """
                INSERT INTO members (name, phone, email, plan, fee, discount, joining_date, expiry_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [(name, phone, email, plan, fee, 0, joining_date, expiry_date) for name, phone, email, plan, fee, joining_date, expiry_date in members],
            )


def get_member_status(expiry_date):
    today = date.today()
    expiry = parse_date(expiry_date)
    if expiry is None:
        return "Unknown"

    if expiry < today:
        return "Expired"
    if expiry == today:
        return "Expiring Today"
    return "Active"


@app.route("/")
def home_page():
    return render_template("home.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if username == "admin" and password == "admin123":
            session["logged_in"] = True
            session["username"] = username
            flash("Login successful! Welcome back.", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid username or password. Try admin / admin123", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        plan = normalize_plan(request.form.get("plan", ""))
        fee = request.form.get("fee", "0").strip()
        discount = request.form.get("discount", "0").strip()
        joining_date = request.form.get("joining_date", "").strip()
        expiry_date = request.form.get("expiry_date", "").strip()

        if not all([name, plan, fee, joining_date, expiry_date]):
            flash("Please fill all required fields.", "danger")
        elif parse_date(joining_date) is None or parse_date(expiry_date) is None:
            flash("Please provide valid YYYY-MM-DD dates.", "danger")
        else:
            try:
                fee_value = float(fee)
                discount_value = float(discount)
            except ValueError:
                flash("Fee and discount must be valid numbers.", "danger")
                fee_value = None

            if fee_value is not None:
                final_fee = max(0.0, fee_value - discount_value)
                with get_db_connection() as conn:
                    conn.execute(
                        """
                        INSERT INTO members (name, phone, email, plan, fee, discount, joining_date, expiry_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (name, phone, email, plan, final_fee, discount_value, joining_date, expiry_date),
                    )
                flash("Member added successfully with discount applied.", "success")
                return redirect(url_for("dashboard"))

    today = date.today()
    default_joining_date = today.isoformat()
    default_expiry_date = (today + timedelta(days=30)).isoformat()

    with get_db_connection() as conn:
        members = conn.execute("SELECT * FROM members ORDER BY expiry_date ASC").fetchall()

    member_rows = []
    expiring_members = []
    gold_members = []
    platinum_members = []
    total_fee = 0.0
    expiring_soon = 0

    for row in members:
        status = get_member_status(row["expiry_date"])
        expiry = parse_date(row["expiry_date"])
        member_data = {
            "id": row["id"],
            "name": row["name"],
            "phone": row["phone"],
            "email": row["email"],
            "plan": normalize_plan(row["plan"]),
            "fee": row["fee"],
            "discount": row["discount"],
            "joining_date": row["joining_date"],
            "expiry_date": row["expiry_date"],
            "status": status,
        }

        if expiry is not None and expiry <= today + timedelta(days=7) and expiry >= today:
            expiring_soon += 1
            expiring_members.append({
                "id": row["id"],
                "name": row["name"],
                "plan": member_data["plan"],
                "expiry_date": row["expiry_date"],
                "status": status,
            })

        if member_data["plan"] == "Gold":
            gold_members.append(member_data)
        elif member_data["plan"] == "Platinum":
            platinum_members.append(member_data)

        total_fee += float(row["fee"])
        member_rows.append(member_data)

    return render_template(
        "dashboard.html",
        members=member_rows,
        total_members=len(member_rows),
        total_fee=total_fee,
        expiring_soon=expiring_soon,
        expiring_members=expiring_members,
        gold_members=gold_members,
        platinum_members=platinum_members,
        today=today,
        default_joining_date=default_joining_date,
        default_expiry_date=default_expiry_date,
        username=session.get("username", "Admin"),
    )


@app.route("/edit_member/<int:member_id>", methods=["GET", "POST"])
def edit_member(member_id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    with get_db_connection() as conn:
        member = conn.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()

    if member is None:
        flash("Member not found.", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        plan = normalize_plan(request.form.get("plan", ""))
        fee = request.form.get("fee", "0").strip()
        discount = request.form.get("discount", "0").strip()
        joining_date = request.form.get("joining_date", "").strip()
        expiry_date = request.form.get("expiry_date", "").strip()

        if not all([name, plan, fee, joining_date, expiry_date]):
            flash("Please fill all required fields.", "danger")
        elif parse_date(joining_date) is None or parse_date(expiry_date) is None:
            flash("Please provide valid YYYY-MM-DD dates.", "danger")
        else:
            try:
                fee_value = float(fee)
                discount_value = float(discount)
            except ValueError:
                flash("Fee and discount must be valid numbers.", "danger")
                fee_value = None

            if fee_value is not None:
                final_fee = max(0.0, fee_value - discount_value)
                with get_db_connection() as conn:
                    conn.execute(
                        """
                        UPDATE members
                        SET name = ?, phone = ?, email = ?, plan = ?, fee = ?, discount = ?, joining_date = ?, expiry_date = ?
                        WHERE id = ?
                        """,
                        (name, phone, email, plan, final_fee, discount_value, joining_date, expiry_date, member_id),
                    )
                flash("Member details updated successfully with discount applied.", "success")
                return redirect(url_for("dashboard"))

    return render_template("edit_member.html", member=dict(member), username=session.get("username", "Admin"))


@app.route("/renew_member/<int:member_id>", methods=["POST"])
def renew_member(member_id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    with get_db_connection() as conn:
        member = conn.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()
        if member is None:
            flash("Member not found.", "danger")
            return redirect(url_for("dashboard"))

        current_expiry = datetime.strptime(member["expiry_date"], "%Y-%m-%d").date()
        new_expiry = current_expiry + timedelta(days=30)
        conn.execute(
            "UPDATE members SET expiry_date = ? WHERE id = ?",
            (new_expiry.isoformat(), member_id),
        )

    flash(f"Membership renewed for {member['name']} until {new_expiry.isoformat()}. Details are now filled automatically.", "success")
    return redirect(url_for("edit_member", member_id=member_id))


@app.route("/delete_member/<int:member_id>", methods=["POST"])
def delete_member(member_id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    with get_db_connection() as conn:
        conn.execute("DELETE FROM members WHERE id = ?", (member_id,))
    flash("Member deleted successfully.", "info")
    return redirect(url_for("dashboard"))


init_db()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
