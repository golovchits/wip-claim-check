import os

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


def connect():
    # dict_row makes each row a dict, so code reads row["claim"] instead of row[4].
    return psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=5, row_factory=dict_row)


def create_table():
    with open("schema.sql") as f:
        schema = f.read()
    with connect() as conn:
        conn.execute(schema)


def save_review(filename, pdf, claim, passages, verdict, explanation, cited_ids, flags):
    # Jsonb tells psycopg to send Python lists and dicts as JSON.
    with connect() as conn:
        row = conn.execute(
            """
            INSERT INTO reviews (filename, pdf, claim, passages, verdict, explanation, cited_ids, flags)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (filename, pdf, claim, Jsonb(passages), verdict, explanation, Jsonb(cited_ids), Jsonb(flags)),
        ).fetchone()
    return row["id"]


def get_review(review_id):
    with connect() as conn:
        return conn.execute("SELECT * FROM reviews WHERE id = %s", (review_id,)).fetchone()


def list_reviews():
    # Leaves out the PDF bytes and passages: the list page only needs these columns.
    with connect() as conn:
        return conn.execute(
            "SELECT id, created_at, claim, verdict, status FROM reviews ORDER BY id DESC"
        ).fetchall()


def set_decision(review_id, status, note):
    with connect() as conn:
        conn.execute(
            "UPDATE reviews SET status = %s, reviewer_note = %s WHERE id = %s",
            (status, note, review_id),
        )
