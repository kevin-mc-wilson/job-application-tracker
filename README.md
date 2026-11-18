# Job Application Tracker

A full-stack web application for tracking a job search: the companies you're interested in, the jobs they post, the applications you submit, and the people you know there. It also includes a **Job Match** tool that ranks jobs by how well they fit your skills.

Built for COP4751 with **Python/Flask**, **MySQL**, and **HTML/CSS (Bootstrap 5)**.

## Features

- **Dashboard** – totals for applications, jobs, companies and contacts, applications by status, and the five most recent applications.
- **Companies, Jobs, Applications, Contacts** – full CRUD (create, list, edit, delete with confirmation) for all four tables, with server-side validation.
- **Job Match** – allows you to enter your skills (e.g. `Python, SQL, Flask`) and see jobs ranked by match percentage, with the skills you're missing.
- **JSON columns** – job requirements and interview details are stored as MySQL `JSON`.

## Tech Stack

| Layer    | Technology                                   |
|----------|----------------------------------------------|
| Database | MySQL 8+                                     |
| Backend  | Python 3 with Flask, `mysql-connector-python` |
| Frontend | Jinja2 templates, HTML, CSS, Bootstrap 5      |

## Project Structure

```
job-application-tracker/
├── app.py            # Flask app: all routes and the Job Match algorithm
├── database.py       # get_db(): MySQL connection from environment variables
├── schema.sql        # Creates the database, 4 tables, and sample data
├── requirements.txt  # Python dependencies
├── .env.example      # Template for local configuration
├── templates/        # Jinja2 HTML templates
├── static/style.css  # Custom styling
├── AI_USAGE.md       # GenAI documentation
└── README.md
```

## Setup

### Prerequisites

- Python 3.9+
- MySQL 8+ installed and running
- Internet access (Bootstrap, Bootstrap Icons and Google Fonts load from CDNs)

### 1. Clone the repository

```bash
git clone https://github.com/kevin-mc-wilson/job-application-tracker.git
cd job-application-tracker
```

### 2. Create a virtual environment and install dependencies

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure the database connection

Copy the example file and put in your MySQL password:

```bash
cp .env.example .env
```

Then edit `.env`:

```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=job_tracker
```

If your password contains `#` or spaces, wrap it in quotes. `.env` is git-ignored, so your password is never committed.
Optionally set `APP_USER_NAME=Your Name` to personalize the dashboard greeting, and `SECRET_KEY` to any long random string.

### 4. Create the database

```bash
mysql -u root -p < schema.sql
```

> **Warning:** `schema.sql` starts with `DROP DATABASE IF EXISTS job_tracker`, so running it **erases and recreates** the `job_tracker` database, including any data you've added.

On macOS, if `mysql` isn't found, use the full path: `/usr/local/mysql/bin/mysql -u root -p < schema.sql`.
Alternatively, open `schema.sql` in MySQL Workbench and run the whole script.

The script loads sample data (3 companies, 3 jobs, 3 applications, 3 contacts) so every page has something to show.

### 5. Run the app

```bash
python app.py
```

Open **http://localhost:5001** in your browser.

## Using the App

- Use the sidebar to move between **Dashboard, Companies, Jobs, Applications, Contacts** and **Job Match**.
- Add a company before adding jobs or contacts, and a job before adding an application. Each record belongs to its parent.
- **Deleting cascades.** Deleting a company also deletes its jobs and contacts, and deleting a job also deletes its applications. The confirmation prompt tells you how many records are affected.
- When adding a job, enter **Required skills** as comma-separated text (`Python, SQL, Flask`). They're stored as JSON in `jobs.requirements`.

### Job Match

Enter your skills on the Job Match page. For each job, the app compares your skills (case-insensitive) with the job's required skills:

```
match % = skills you have ÷ skills the job requires × 100
```

Jobs are ranked from highest to lowest match, each showing the skills you have and are missing:

```
1. Software Engineer at Tech Innovators Inc. – 75% (3/4 skills)
   Missing: Data Structures
```

Jobs with no listed skills can't be scored and are left out (the page says how many).

## Database Schema

Four tables, linked by foreign keys with `ON DELETE CASCADE`:

```
companies (company_id PK, company_name, industry, website, city, state, notes)
   ├── jobs (job_id PK, company_id FK, job_title, job_type ENUM, salary_min, salary_max,
   │         job_url, date_posted, requirements JSON)
   │      └── applications (application_id PK, job_id FK, application_date, status ENUM,
   │                        resume_version, cover_letter_sent, interview_data JSON)
   └── contacts (contact_id PK, company_id FK, contact_name, title, email, phone,
                 linkedin_url, notes)
```

JSON shapes used by the app:

```json
// jobs.requirements
{"skills": ["Python", "SQL", "Flask"], "experience": "3+ years"}

// applications.interview_data
{"interview_date": "2025-02-10", "interviewers": ["Jane Smith"], "feedback": "Positive"}
```

## Troubleshooting

| Problem | Fix |
|---|---|
| `Access denied for user 'root'` | Check `DB_PASSWORD` in `.env`. |
| `Unknown database 'job_tracker'` | Run `mysql -u root -p < schema.sql`. |
| `mysql: command not found` | Use the full path to the MySQL client (see step 4) or add it to your `PATH`. |
| Dashboard shows old or unexpected data | Re-run `schema.sql` to reset the database. |

## GenAI Disclosure

AI tools were used during development. See [AI_USAGE.md](AI_USAGE.md) for details.
