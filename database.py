"""Database connection helpers for the Job Application Tracker.

Connection settings come from environment variables so that no password is
committed to GitHub. Optionally, put them in a local `.env` file (see
`.env.example`); it is loaded automatically if python-dotenv is installed.
"""
import os

import mysql.connector

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # python-dotenv is optional
    pass


def get_db():
    """Return a new MySQL connection using environment variables."""
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT", "3306")),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "job_tracker"),
    )
