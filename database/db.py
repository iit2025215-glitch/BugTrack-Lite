import sqlite3
from datetime import datetime

DATABASE = "bugtrack.db"


def connect():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def initialize_database():
    with connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bugs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                project TEXT NOT NULL,
                severity TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Open',
                reported_by TEXT DEFAULT 'You',
                assigned_to TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(bugs)")
        }

        migrations = {
            "reported_by": "TEXT DEFAULT 'You'",
            "assigned_to": "TEXT DEFAULT ''",
            "created_at": "TEXT",
            "updated_at": "TEXT",
        }

        for name, declaration in migrations.items():
            if name not in columns:
                conn.execute(
                    f"ALTER TABLE bugs ADD COLUMN {name} {declaration}"
                )

        stamp = now()

        conn.execute(
            "UPDATE bugs SET created_at = COALESCE(created_at, ?)",
            (stamp,)
        )

        conn.execute(
            """
            UPDATE bugs
            SET updated_at = COALESCE(updated_at, created_at, ?)
            """,
            (stamp,)
        )

        conn.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bug_id INTEGER NOT NULL,
                author TEXT NOT NULL,
                body TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (bug_id)
                    REFERENCES bugs(id)
                    ON DELETE CASCADE
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bug_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (bug_id)
                    REFERENCES bugs(id)
                    ON DELETE CASCADE
            )
        """)


def log_activity(conn, bug_id, message):
    conn.execute(
        """
        INSERT INTO activity (bug_id, message, created_at)
        VALUES (?, ?, ?)
        """,
        (bug_id, message, now())
    )


def create_bug(data):
    stamp = now()

    with connect() as conn:
        cur = conn.execute("""
            INSERT INTO bugs (
                title,
                description,
                project,
                severity,
                status,
                reported_by,
                assigned_to,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, 'Open', ?, ?, ?, ?)
        """, (
            data["title"].strip(),
            data["description"].strip(),
            data["project"].strip(),
            data["severity"],
            str(data.get("reported_by", "You")).strip() or "You",
            str(data.get("assigned_to", "")).strip(),
            stamp,
            stamp,
        ))

        bug_id = cur.lastrowid

        log_activity(conn, bug_id, "Issue created")

        return bug_id


def get_all_bugs(
    search="",
    status="",
    severity="",
    project="",
    sort="newest"
):
    order = {
        "newest": "created_at DESC",
        "oldest": "created_at ASC",
        "title": "title COLLATE NOCASE ASC",
        "severity": """
            CASE severity
                WHEN 'Critical' THEN 1
                WHEN 'High' THEN 2
                WHEN 'Medium' THEN 3
                ELSE 4
            END
        """,
        "updated": "updated_at DESC",
    }.get(sort, "created_at DESC")

    query = "SELECT * FROM bugs WHERE 1=1"
    args = []

    if search:
        like = f"%{search}%"

        query += """
            AND (
                title LIKE ?
                OR description LIKE ?
                OR project LIKE ?
                OR assigned_to LIKE ?
            )
        """

        args.extend([like, like, like, like])

    if status:
        query += " AND status = ?"
        args.append(status)

    if severity:
        query += " AND severity = ?"
        args.append(severity)

    if project:
        query += " AND project = ?"
        args.append(project)

    query += f" ORDER BY {order}"

    with connect() as conn:
        rows = conn.execute(query, args).fetchall()

        return [dict(row) for row in rows]


def get_bug(bug_id):
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM bugs WHERE id = ?",
            (bug_id,)
        ).fetchone()

        return dict(row) if row else None


def get_bug_statistics():
    with connect() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM bugs"
        ).fetchone()[0]

        open_count = conn.execute(
            "SELECT COUNT(*) FROM bugs WHERE status='Open'"
        ).fetchone()[0]

        progress = conn.execute(
            "SELECT COUNT(*) FROM bugs WHERE status='In Progress'"
        ).fetchone()[0]

        resolved = conn.execute(
            "SELECT COUNT(*) FROM bugs WHERE status='Resolved'"
        ).fetchone()[0]

    return {
        "total": total,
        "open": open_count,
        "progress": progress,
        "resolved": resolved,
    }


def get_projects():
    with connect() as conn:
        rows = conn.execute("""
            SELECT DISTINCT project
            FROM bugs
            WHERE project != ''
            ORDER BY project COLLATE NOCASE
        """).fetchall()

        return [row[0] for row in rows]


def update_bug(bug_id, data):
    with connect() as conn:
        conn.execute("""
            UPDATE bugs
            SET title = ?,
                description = ?,
                project = ?,
                severity = ?,
                assigned_to = ?,
                updated_at = ?
            WHERE id = ?
        """, (
            data["title"].strip(),
            data["description"].strip(),
            data["project"].strip(),
            data["severity"],
            str(data.get("assigned_to", "")).strip(),
            now(),
            bug_id,
        ))

        log_activity(conn, bug_id, "Issue details edited")


def update_bug_status(bug_id, status):
    with connect() as conn:
        old = conn.execute(
            "SELECT status FROM bugs WHERE id = ?",
            (bug_id,)
        ).fetchone()

        conn.execute(
            """
            UPDATE bugs
            SET status = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, now(), bug_id)
        )

        if old and old["status"] != status:
            log_activity(
                conn,
                bug_id,
                f"Status changed: {old['status']} → {status}"
            )


def delete_bug(bug_id):
    with connect() as conn:
        conn.execute(
            "DELETE FROM comments WHERE bug_id = ?",
            (bug_id,)
        )

        conn.execute(
            "DELETE FROM activity WHERE bug_id = ?",
            (bug_id,)
        )

        conn.execute(
            "DELETE FROM bugs WHERE id = ?",
            (bug_id,)
        )


def add_comment(bug_id, author, body):
    with connect() as conn:
        conn.execute("""
            INSERT INTO comments (
                bug_id,
                author,
                body,
                created_at
            )
            VALUES (?, ?, ?, ?)
        """, (bug_id, author, body, now()))

        log_activity(
            conn,
            bug_id,
            f"Comment added by {author}"
        )


def get_bug_comments(bug_id):
    with connect() as conn:
        rows = conn.execute("""
            SELECT *
            FROM comments
            WHERE bug_id = ?
            ORDER BY id DESC
        """, (bug_id,)).fetchall()

        return [dict(row) for row in rows]


def get_bug_activity(bug_id):
    with connect() as conn:
        rows = conn.execute("""
            SELECT *
            FROM activity
            WHERE bug_id = ?
            ORDER BY id DESC
        """, (bug_id,)).fetchall()

        return [dict(row) for row in rows]