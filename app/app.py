import os

import pymysql
from pymysql.constants import CLIENT
from flask import Flask, jsonify, request

app = Flask(__name__)


def get_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "notesuser"),
        password=os.getenv("DB_PASSWORD", "notespass"),
        database=os.getenv("DB_NAME", "notesdb"),
        cursorclass=pymysql.cursors.DictCursor,
        client_flag=CLIENT.FOUND_ROWS,
    )


def init_db():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS notes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(100) NOT NULL,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        conn.commit()
    finally:
        conn.close()


@app.route("/")
def home():
    return jsonify(message="Notes app is running")


@app.route("/health")
def health():
    return jsonify(status="healthy"), 200


@app.route("/notes", methods=["POST"])
def create_note():
    data = request.get_json()
    if not data or not data.get("title"):
        return jsonify(error="title is required"), 400

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO notes (title, content) VALUES (%s, %s)",
                (data["title"], data.get("content", "")),
            )
        conn.commit()
        return jsonify(message="note created", id=cur.lastrowid), 201
    finally:
        conn.close()


@app.route("/notes", methods=["GET"])
def list_notes():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, title, content, created_at FROM notes")
            return jsonify(cur.fetchall()), 200
    finally:
        conn.close()
@app.route("/notes/<int:note_id>", methods=["PUT"])
def update_note(note_id):
    data = request.get_json()
    if not data or not data.get("title"):
        return jsonify(error="title is required"), 400

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE notes SET title = %s, content = %s WHERE id = %s",
                (data["title"], data.get("content", ""), note_id),
            )
            if cur.rowcount == 0:
                return jsonify(error="note not found"), 404
        conn.commit()
        return jsonify(message="note updated"), 200
    finally:
        conn.close()


@app.route("/notes/<int:note_id>", methods=["DELETE"])
def delete_note(note_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM notes WHERE id = %s", (note_id,))
            if cur.rowcount == 0:
                return jsonify(error="note not found"), 404
        conn.commit()
        return jsonify(message="note deleted"), 200
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
