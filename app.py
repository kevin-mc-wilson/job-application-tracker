import json
import os
import re
from datetime import date, datetime

from flask import Flask, abort, flash, redirect, render_template, request, url_for
from database import get_db

app = Flask(__name__)
# Needed for flash messages. Set SECRET_KEY in .env for anything beyond local dev.
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-secret-key")


def greeting_for(hour):
    if hour < 12:
        return "Good morning"
    if hour < 18:
        return "Good afternoon"
    return "Good evening"


@app.route("/")
def dashboard():
    conn = get_db()

    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM companies)    AS companies,
                (SELECT COUNT(*) FROM jobs)         AS jobs,
                (SELECT COUNT(*) FROM applications) AS applications,
                (SELECT COUNT(*) FROM contacts)     AS contacts
            """
        )
        stats = cursor.fetchone()

        cursor.execute(
            """
            SELECT status, COUNT(*) AS count
            FROM applications
            GROUP BY status
            ORDER BY count DESC
            """
        )
        status_counts = cursor.fetchall()

        cursor.execute(
            """
            SELECT a.application_id, a.application_date, a.status,
                   j.job_title, c.company_name
            FROM applications a
            JOIN jobs j ON a.job_id = j.job_id
            JOIN companies c ON j.company_id = c.company_id
            ORDER BY a.application_date DESC, a.application_id DESC
            LIMIT 5
            """
        )
        recent = cursor.fetchall()
    finally:
        conn.close()
    return render_template(
        "dashboard.html",
        stats=stats,
        status_counts=status_counts,
        recent=recent,
        greeting=greeting_for(datetime.now().hour),
        today=datetime.now().strftime("%A, %-d %B %Y"),
        user_name=os.environ.get("APP_USER_NAME", "").strip(),
    )


# ---------------------------------------------------------------- Companies

COMPANY_FIELDS = ["company_name", "industry", "website", "city", "state", "notes"]
COMPANY_MAX_LEN = {
    "company_name": 100,
    "industry": 50,
    "website": 200,
    "city": 50,
    "state": 50,
}


def read_company_form():
    """Return (values, errors) from the submitted company form."""
    values = {f: request.form.get(f, "").strip() for f in COMPANY_FIELDS}
    errors = []
    if not values["company_name"]:
        errors.append("Company name is required.")
    for field, limit in COMPANY_MAX_LEN.items():
        if len(values[field]) > limit:
            label = field.replace("_", " ").capitalize()
            errors.append(f"{label} must be {limit} characters or fewer.")
    if values["website"] and not values["website"].startswith(("http://", "https://")):
        errors.append("Website must start with http:// or https://.")
    # Store empty optional fields as NULL
    for field in COMPANY_FIELDS:
        if field != "company_name" and not values[field]:
            values[field] = None
    return values, errors


def get_company_or_404(cursor, company_id):
    cursor.execute("SELECT * FROM companies WHERE company_id = %s", (company_id,))
    company = cursor.fetchone()
    if company is None:
        abort(404)
    return company


@app.route("/companies")
def companies():
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT c.*,
                   (SELECT COUNT(*) FROM jobs j WHERE j.company_id = c.company_id) AS job_count,
                   (SELECT COUNT(*) FROM contacts ct WHERE ct.company_id = c.company_id) AS contact_count
            FROM companies c
            ORDER BY c.company_name
            """
        )
        rows = cursor.fetchall()
    finally:
        conn.close()
    return render_template("companies.html", companies=rows)


@app.route("/companies/add", methods=["GET", "POST"])
def add_company():
    if request.method == "POST":
        values, errors = read_company_form()
        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("company_form.html", company=values, editing=False)
        conn = get_db()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO companies (company_name, industry, website, city, state, notes)
                VALUES (%(company_name)s, %(industry)s, %(website)s, %(city)s, %(state)s, %(notes)s)
                """,
                values,
            )
            conn.commit()
        finally:
            conn.close()
        flash(f"Added company “{values['company_name']}”.", "success")
        return redirect(url_for("companies"))
    return render_template("company_form.html", company={}, editing=False)


@app.route("/companies/<int:company_id>/edit", methods=["GET", "POST"])
def edit_company(company_id):
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        company = get_company_or_404(cursor, company_id)
        if request.method == "POST":
            values, errors = read_company_form()
            if errors:
                for e in errors:
                    flash(e, "danger")
                values["company_id"] = company_id
                return render_template("company_form.html", company=values, editing=True)
            values["company_id"] = company_id
            cursor.execute(
                """
                UPDATE companies
                SET company_name = %(company_name)s, industry = %(industry)s,
                    website = %(website)s, city = %(city)s, state = %(state)s,
                    notes = %(notes)s
                WHERE company_id = %(company_id)s
                """,
                values,
            )
            conn.commit()
            flash(f"Updated company “{values['company_name']}”.", "success")
            return redirect(url_for("companies"))
    finally:
        conn.close()
    return render_template("company_form.html", company=company, editing=True)


@app.route("/companies/<int:company_id>/delete", methods=["POST"])
def delete_company(company_id):
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        company = get_company_or_404(cursor, company_id)
        cursor.execute("DELETE FROM companies WHERE company_id = %s", (company_id,))
        conn.commit()
    finally:
        conn.close()
    flash(f"Deleted company “{company['company_name']}” and its related jobs and contacts.", "warning")
    return redirect(url_for("companies"))


# --------------------------------------------------------------------- Jobs

JOB_TYPES = ["Full-time", "Part-time", "Contract", "Internship"]


def parse_requirements(raw):
    """Normalize a requirements JSON value into {"skills": [...], "experience": str}.

    MySQL JSON columns come back from the connector as str, so decode first.
    A plain list (e.g. ["Python", "SQL"]) is accepted as the skills list.
    """
    if raw is None or raw == "":
        return {"skills": [], "experience": ""}
    if isinstance(raw, (str, bytes)):
        try:
            raw = json.loads(raw)
        except ValueError:
            return {"skills": [], "experience": ""}
    if isinstance(raw, list):
        return {"skills": [str(s) for s in raw], "experience": ""}
    if isinstance(raw, dict):
        skills = raw.get("skills") or []
        return {
            "skills": [str(s) for s in skills] if isinstance(skills, list) else [],
            "experience": str(raw.get("experience") or ""),
        }
    return {"skills": [], "experience": ""}


def split_list(text):
    """'Python, SQL,python' -> ['Python', 'SQL'] (trimmed, de-duplicated)."""
    seen, skills = set(), []
    for part in text.split(","):
        skill = part.strip()
        if skill and skill.lower() not in seen:
            seen.add(skill.lower())
            skills.append(skill)
    return skills


def get_company_choices(cursor):
    cursor.execute("SELECT company_id, company_name FROM companies ORDER BY company_name")
    return cursor.fetchall()


def read_job_form(valid_company_ids):
    """Return (values, errors) from the submitted job form.

    `values` holds DB-ready fields plus 'skills_text'/'experience' so the form
    can be re-displayed exactly as typed.
    """
    form = request.form
    errors = []

    def text(name):
        return form.get(name, "").strip()

    values = {
        "company_id": None,
        "job_title": text("job_title"),
        "job_type": text("job_type") or None,
        "salary_min": None,
        "salary_max": None,
        "job_url": text("job_url") or None,
        "date_posted": None,
        "skills_text": text("skills"),
        "experience": text("experience"),
    }

    # Company (must exist)
    try:
        company_id = int(text("company_id"))
    except ValueError:
        company_id = None
    if company_id in valid_company_ids:
        values["company_id"] = company_id
    else:
        errors.append("Please choose a company.")

    # Title
    if not values["job_title"]:
        errors.append("Job title is required.")
    elif len(values["job_title"]) > 100:
        errors.append("Job title must be 100 characters or fewer.")

    # Job type
    if values["job_type"] is not None and values["job_type"] not in JOB_TYPES:
        errors.append("Invalid job type.")

    # Salaries
    for field, label in (("salary_min", "Minimum salary"), ("salary_max", "Maximum salary")):
        raw = text(field)
        if raw:
            try:
                number = int(raw)
                if number < 0:
                    raise ValueError
                values[field] = number
            except ValueError:
                errors.append(f"{label} must be a whole number of 0 or more.")
                values[field] = raw  # keep what was typed for redisplay
    if (
        isinstance(values["salary_min"], int)
        and isinstance(values["salary_max"], int)
        and values["salary_min"] > values["salary_max"]
    ):
        errors.append("Minimum salary cannot be greater than maximum salary.")

    # URL
    if values["job_url"]:
        if len(values["job_url"]) > 300:
            errors.append("Job URL must be 300 characters or fewer.")
        elif not values["job_url"].startswith(("http://", "https://")):
            errors.append("Job URL must start with http:// or https://.")

    # Date posted
    raw_date = text("date_posted")
    if raw_date:
        try:
            values["date_posted"] = date.fromisoformat(raw_date)
        except ValueError:
            errors.append("Date posted must be a valid date.")
            values["date_posted"] = raw_date

    # Requirements -> JSON
    skills = split_list(values["skills_text"])
    requirements = {}
    if skills:
        requirements["skills"] = skills
    if values["experience"]:
        requirements["experience"] = values["experience"]
    values["requirements"] = json.dumps(requirements) if requirements else None

    return values, errors


def job_to_form_values(job):
    """Turn a DB row into the dict the form template expects."""
    req = parse_requirements(job["requirements"])
    job = dict(job)
    job["skills_text"] = ", ".join(req["skills"])
    job["experience"] = req["experience"]
    return job


def get_job_or_404(cursor, job_id):
    cursor.execute("SELECT * FROM jobs WHERE job_id = %s", (job_id,))
    job = cursor.fetchone()
    if job is None:
        abort(404)
    return job


@app.route("/jobs")
def jobs():
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT j.*, c.company_name,
                   (SELECT COUNT(*) FROM applications a WHERE a.job_id = j.job_id) AS application_count
            FROM jobs j
            JOIN companies c ON j.company_id = c.company_id
            ORDER BY j.date_posted DESC, j.job_id DESC
            """
        )
        rows = cursor.fetchall()
    finally:
        conn.close()
    for row in rows:
        row["skills"] = parse_requirements(row["requirements"])["skills"]
    return render_template("jobs.html", jobs=rows)


@app.route("/jobs/add", methods=["GET", "POST"])
def add_job():
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        companies = get_company_choices(cursor)
        if not companies:
            flash("Add a company first — every job belongs to a company.", "warning")
            return redirect(url_for("add_company"))

        if request.method == "POST":
            values, errors = read_job_form({c["company_id"] for c in companies})
            if errors:
                for e in errors:
                    flash(e, "danger")
                return render_template(
                    "job_form.html", job=values, companies=companies,
                    job_types=JOB_TYPES, editing=False,
                )
            cursor.execute(
                """
                INSERT INTO jobs (company_id, job_title, job_type, salary_min, salary_max,
                                  job_url, date_posted, requirements)
                VALUES (%(company_id)s, %(job_title)s, %(job_type)s, %(salary_min)s,
                        %(salary_max)s, %(job_url)s, %(date_posted)s, %(requirements)s)
                """,
                values,
            )
            conn.commit()
            flash(f"Added job “{values['job_title']}”.", "success")
            return redirect(url_for("jobs"))
    finally:
        conn.close()
    return render_template(
        "job_form.html", job={"company_id": request.args.get("company_id", type=int)},
        companies=companies, job_types=JOB_TYPES, editing=False,
    )


@app.route("/jobs/<int:job_id>/edit", methods=["GET", "POST"])
def edit_job(job_id):
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        job = get_job_or_404(cursor, job_id)
        companies = get_company_choices(cursor)

        if request.method == "POST":
            values, errors = read_job_form({c["company_id"] for c in companies})
            values["job_id"] = job_id
            if errors:
                for e in errors:
                    flash(e, "danger")
                return render_template(
                    "job_form.html", job=values, companies=companies,
                    job_types=JOB_TYPES, editing=True,
                )
            cursor.execute(
                """
                UPDATE jobs
                SET company_id = %(company_id)s, job_title = %(job_title)s,
                    job_type = %(job_type)s, salary_min = %(salary_min)s,
                    salary_max = %(salary_max)s, job_url = %(job_url)s,
                    date_posted = %(date_posted)s, requirements = %(requirements)s
                WHERE job_id = %(job_id)s
                """,
                values,
            )
            conn.commit()
            flash(f"Updated job “{values['job_title']}”.", "success")
            return redirect(url_for("jobs"))
    finally:
        conn.close()
    return render_template(
        "job_form.html", job=job_to_form_values(job), companies=companies,
        job_types=JOB_TYPES, editing=True,
    )


@app.route("/jobs/<int:job_id>/delete", methods=["POST"])
def delete_job(job_id):
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        job = get_job_or_404(cursor, job_id)
        cursor.execute("DELETE FROM jobs WHERE job_id = %s", (job_id,))
        conn.commit()
    finally:
        conn.close()
    flash(f"Deleted job “{job['job_title']}” and its applications.", "warning")
    return redirect(url_for("jobs"))


# ------------------------------------------------------------- Applications

APPLICATION_STATUSES = ["Applied", "Screening", "Interview", "Offer", "Rejected", "Withdrawn"]


def parse_interview_data(raw):
    """Normalize interview_data JSON into
    {"interview_date": str, "interviewers": [...], "feedback": str}."""
    empty = {"interview_date": "", "interviewers": [], "feedback": ""}
    if raw is None or raw == "":
        return empty
    if isinstance(raw, (str, bytes)):
        try:
            raw = json.loads(raw)
        except ValueError:
            return empty
    if not isinstance(raw, dict):
        return empty
    interviewers = raw.get("interviewers") or []
    return {
        "interview_date": str(raw.get("interview_date") or ""),
        "interviewers": [str(i) for i in interviewers] if isinstance(interviewers, list) else [],
        "feedback": str(raw.get("feedback") or ""),
    }


def get_job_choices(cursor):
    cursor.execute(
        """
        SELECT j.job_id, j.job_title, c.company_name
        FROM jobs j JOIN companies c ON j.company_id = c.company_id
        ORDER BY c.company_name, j.job_title
        """
    )
    return cursor.fetchall()


def read_application_form(valid_job_ids):
    """Return (values, errors) from the submitted application form."""
    form = request.form
    errors = []

    def text(name):
        return form.get(name, "").strip()

    values = {
        "job_id": None,
        "application_date": None,
        "status": text("status"),
        "resume_version": text("resume_version") or None,
        "cover_letter_sent": 1 if form.get("cover_letter_sent") else 0,
        "interviewers_text": text("interviewers"),
        "interview_date": text("interview_date"),
        "feedback": text("feedback"),
    }

    # Job (must exist)
    try:
        job_id = int(text("job_id"))
    except ValueError:
        job_id = None
    if job_id in valid_job_ids:
        values["job_id"] = job_id
    else:
        errors.append("Please choose a job.")

    # Application date (required)
    raw_date = text("application_date")
    if not raw_date:
        errors.append("Application date is required.")
    else:
        try:
            values["application_date"] = date.fromisoformat(raw_date)
        except ValueError:
            errors.append("Application date must be a valid date.")
            values["application_date"] = raw_date

    # Status
    if values["status"] not in APPLICATION_STATUSES:
        errors.append("Invalid status.")

    # Resume version
    if values["resume_version"] and len(values["resume_version"]) > 50:
        errors.append("Resume version must be 50 characters or fewer.")

    # Interview date (optional)
    if values["interview_date"]:
        try:
            date.fromisoformat(values["interview_date"])
        except ValueError:
            errors.append("Interview date must be a valid date.")

    # Interview data -> JSON
    interview = {}
    if values["interview_date"]:
        interview["interview_date"] = values["interview_date"]
    interviewers = split_list(values["interviewers_text"])
    if interviewers:
        interview["interviewers"] = interviewers
    if values["feedback"]:
        interview["feedback"] = values["feedback"]
    values["interview_data"] = json.dumps(interview) if interview else None

    return values, errors


def application_to_form_values(app_row):
    """Turn a DB row into the dict the form template expects."""
    data = parse_interview_data(app_row["interview_data"])
    app_row = dict(app_row)
    app_row["interview_date"] = data["interview_date"]
    app_row["interviewers_text"] = ", ".join(data["interviewers"])
    app_row["feedback"] = data["feedback"]
    return app_row


def get_application_or_404(cursor, application_id):
    cursor.execute("SELECT * FROM applications WHERE application_id = %s", (application_id,))
    row = cursor.fetchone()
    if row is None:
        abort(404)
    return row


@app.route("/applications")
def applications():
    status_filter = request.args.get("status", "")
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        sql = """
            SELECT a.*, j.job_title, c.company_name
            FROM applications a
            JOIN jobs j ON a.job_id = j.job_id
            JOIN companies c ON j.company_id = c.company_id
        """
        params = ()
        if status_filter in APPLICATION_STATUSES:
            sql += " WHERE a.status = %s"
            params = (status_filter,)
        sql += " ORDER BY a.application_date DESC, a.application_id DESC"
        cursor.execute(sql, params)
        rows = cursor.fetchall()
    finally:
        conn.close()
    for row in rows:
        row["interview"] = parse_interview_data(row["interview_data"])
    return render_template(
        "applications.html", applications=rows,
        statuses=APPLICATION_STATUSES, status_filter=status_filter,
    )


@app.route("/applications/add", methods=["GET", "POST"])
def add_application():
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        jobs_list = get_job_choices(cursor)
        if not jobs_list:
            flash("Add a job first — every application is for a job.", "warning")
            return redirect(url_for("add_job"))

        if request.method == "POST":
            values, errors = read_application_form({j["job_id"] for j in jobs_list})
            if errors:
                for e in errors:
                    flash(e, "danger")
                return render_template(
                    "application_form.html", application=values, jobs=jobs_list,
                    statuses=APPLICATION_STATUSES, editing=False,
                )
            cursor.execute(
                """
                INSERT INTO applications (job_id, application_date, status, resume_version,
                                          cover_letter_sent, interview_data)
                VALUES (%(job_id)s, %(application_date)s, %(status)s, %(resume_version)s,
                        %(cover_letter_sent)s, %(interview_data)s)
                """,
                values,
            )
            conn.commit()
            flash("Application added.", "success")
            return redirect(url_for("applications"))
    finally:
        conn.close()
    defaults = {
        "job_id": request.args.get("job_id", type=int),
        "application_date": date.today(),
        "status": "Applied",
    }
    return render_template(
        "application_form.html", application=defaults, jobs=jobs_list,
        statuses=APPLICATION_STATUSES, editing=False,
    )


@app.route("/applications/<int:application_id>/edit", methods=["GET", "POST"])
def edit_application(application_id):
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        application = get_application_or_404(cursor, application_id)
        jobs_list = get_job_choices(cursor)

        if request.method == "POST":
            values, errors = read_application_form({j["job_id"] for j in jobs_list})
            values["application_id"] = application_id
            if errors:
                for e in errors:
                    flash(e, "danger")
                return render_template(
                    "application_form.html", application=values, jobs=jobs_list,
                    statuses=APPLICATION_STATUSES, editing=True,
                )
            cursor.execute(
                """
                UPDATE applications
                SET job_id = %(job_id)s, application_date = %(application_date)s,
                    status = %(status)s, resume_version = %(resume_version)s,
                    cover_letter_sent = %(cover_letter_sent)s,
                    interview_data = %(interview_data)s
                WHERE application_id = %(application_id)s
                """,
                values,
            )
            conn.commit()
            flash("Application updated.", "success")
            return redirect(url_for("applications"))
    finally:
        conn.close()
    return render_template(
        "application_form.html", application=application_to_form_values(application),
        jobs=jobs_list, statuses=APPLICATION_STATUSES, editing=True,
    )


@app.route("/applications/<int:application_id>/delete", methods=["POST"])
def delete_application(application_id):
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        get_application_or_404(cursor, application_id)
        cursor.execute("DELETE FROM applications WHERE application_id = %s", (application_id,))
        conn.commit()
    finally:
        conn.close()
    flash("Application deleted.", "warning")
    return redirect(url_for("applications"))


# ----------------------------------------------------------------- Contacts

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^[0-9+()\-.\sxX]+$")
CONTACT_FIELDS = ["contact_name", "title", "email", "phone", "linkedin_url", "notes"]
CONTACT_MAX_LEN = {
    "contact_name": 100,
    "title": 100,
    "email": 100,
    "phone": 20,
    "linkedin_url": 200,
}


def read_contact_form(valid_company_ids):
    """Return (values, errors) from the submitted contact form."""
    errors = []
    values = {f: request.form.get(f, "").strip() for f in CONTACT_FIELDS}
    values["company_id"] = None

    # Company (must exist)
    try:
        company_id = int(request.form.get("company_id", "").strip())
    except ValueError:
        company_id = None
    if company_id in valid_company_ids:
        values["company_id"] = company_id
    else:
        errors.append("Please choose a company.")

    if not values["contact_name"]:
        errors.append("Contact name is required.")

    for field, limit in CONTACT_MAX_LEN.items():
        if len(values[field]) > limit:
            label = field.replace("_", " ").capitalize()
            errors.append(f"{label} must be {limit} characters or fewer.")

    if values["email"] and not EMAIL_RE.match(values["email"]):
        errors.append("Please enter a valid email address.")
    if values["phone"] and not PHONE_RE.match(values["phone"]):
        errors.append("Phone may only contain digits, spaces and + ( ) - . characters.")
    if values["linkedin_url"] and not values["linkedin_url"].startswith(("http://", "https://")):
        errors.append("LinkedIn URL must start with http:// or https://.")

    # Store empty optional fields as NULL
    for field in CONTACT_FIELDS:
        if field != "contact_name" and not values[field]:
            values[field] = None
    return values, errors


def get_contact_or_404(cursor, contact_id):
    cursor.execute("SELECT * FROM contacts WHERE contact_id = %s", (contact_id,))
    contact = cursor.fetchone()
    if contact is None:
        abort(404)
    return contact


@app.route("/contacts")
def contacts():
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT ct.*, c.company_name
            FROM contacts ct
            JOIN companies c ON ct.company_id = c.company_id
            ORDER BY c.company_name, ct.contact_name
            """
        )
        rows = cursor.fetchall()
    finally:
        conn.close()
    return render_template("contacts.html", contacts=rows)


@app.route("/contacts/add", methods=["GET", "POST"])
def add_contact():
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        companies = get_company_choices(cursor)
        if not companies:
            flash("Add a company first — every contact belongs to a company.", "warning")
            return redirect(url_for("add_company"))

        if request.method == "POST":
            values, errors = read_contact_form({c["company_id"] for c in companies})
            if errors:
                for e in errors:
                    flash(e, "danger")
                return render_template(
                    "contact_form.html", contact=values, companies=companies, editing=False
                )
            cursor.execute(
                """
                INSERT INTO contacts (company_id, contact_name, title, email, phone,
                                      linkedin_url, notes)
                VALUES (%(company_id)s, %(contact_name)s, %(title)s, %(email)s,
                        %(phone)s, %(linkedin_url)s, %(notes)s)
                """,
                values,
            )
            conn.commit()
            flash(f"Added contact “{values['contact_name']}”.", "success")
            return redirect(url_for("contacts"))
    finally:
        conn.close()
    return render_template(
        "contact_form.html",
        contact={"company_id": request.args.get("company_id", type=int)},
        companies=companies,
        editing=False,
    )


@app.route("/contacts/<int:contact_id>/edit", methods=["GET", "POST"])
def edit_contact(contact_id):
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        contact = get_contact_or_404(cursor, contact_id)
        companies = get_company_choices(cursor)

        if request.method == "POST":
            values, errors = read_contact_form({c["company_id"] for c in companies})
            values["contact_id"] = contact_id
            if errors:
                for e in errors:
                    flash(e, "danger")
                return render_template(
                    "contact_form.html", contact=values, companies=companies, editing=True
                )
            cursor.execute(
                """
                UPDATE contacts
                SET company_id = %(company_id)s, contact_name = %(contact_name)s,
                    title = %(title)s, email = %(email)s, phone = %(phone)s,
                    linkedin_url = %(linkedin_url)s, notes = %(notes)s
                WHERE contact_id = %(contact_id)s
                """,
                values,
            )
            conn.commit()
            flash(f"Updated contact “{values['contact_name']}”.", "success")
            return redirect(url_for("contacts"))
    finally:
        conn.close()
    return render_template("contact_form.html", contact=contact, companies=companies, editing=True)


@app.route("/contacts/<int:contact_id>/delete", methods=["POST"])
def delete_contact(contact_id):
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        contact = get_contact_or_404(cursor, contact_id)
        cursor.execute("DELETE FROM contacts WHERE contact_id = %s", (contact_id,))
        conn.commit()
    finally:
        conn.close()
    flash(f"Deleted contact “{contact['contact_name']}”.", "warning")
    return redirect(url_for("contacts"))


# ---------------------------------------------------------------- Job Match

def normalize_skill(skill):
    """Case-insensitive, whitespace-insensitive key for comparing skills."""
    return " ".join(skill.lower().split())


def calculate_matches(user_skills, jobs):
    """Rank jobs by how many of their required skills the user has.

    user_skills: list of skill strings entered by the user.
    jobs: rows with job_title, company_name and a 'requirements' JSON value.

    Returns (ranked, no_skills_count). Each ranked item is a dict with
    percent, matched, missing, total and the job fields. Jobs that list no
    skills can't be scored, so they are counted separately instead.
    """
    have = {normalize_skill(s) for s in user_skills}
    ranked, no_skills = [], 0

    for job in jobs:
        required = split_list(", ".join(parse_requirements(job["requirements"])["skills"]))
        if not required:
            no_skills += 1
            continue
        matched = [s for s in required if normalize_skill(s) in have]
        missing = [s for s in required if normalize_skill(s) not in have]
        ranked.append(
            {
                **job,
                "required": required,
                "matched": matched,
                "missing": missing,
                "total": len(required),
                "percent": round(len(matched) / len(required) * 100),
            }
        )

    ranked.sort(key=lambda r: (-r["percent"], -len(r["matched"]), r["job_title"].lower()))
    return ranked, no_skills


@app.route("/job-match")
def job_match():
    skills_text = request.args.get("skills", "").strip()
    user_skills = split_list(skills_text)
    results, no_skills = [], 0

    if user_skills:
        conn = get_db()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT j.job_id, j.job_title, j.job_type, j.salary_min, j.salary_max,
                       j.job_url, j.requirements, c.company_name
                FROM jobs j JOIN companies c ON j.company_id = c.company_id
                """
            )
            jobs_rows = cursor.fetchall()
        finally:
            conn.close()
        results, no_skills = calculate_matches(user_skills, jobs_rows)
    elif "skills" in request.args:
        flash("Enter at least one skill, separated by commas.", "warning")

    return render_template(
        "job_match.html",
        skills_text=skills_text,
        user_skills=user_skills,
        results=results,
        no_skills=no_skills,
        searched=bool(user_skills),
    )


if __name__ == "__main__":
    # Port 5001: macOS AirPlay Receiver occupies port 5000 and answers localhost:5000 with 403.
    app.run(debug=True, port=5001)