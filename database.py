"""
Database for leads.

Also persists a durable last-run summary so the dashboard can show the most
recent full scrape outcome even after restarts.
"""
import json
import os
from typing import Any
from datetime import datetime, timezone
import sqlite3
from contextlib import closing
from config import DB_PATH


def get_conn() -> sqlite3.Connection:
    db_dir = os.path.dirname(os.fspath(DB_PATH))
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with closing(get_conn()) as conn, conn:
        c = conn.cursor()
        c.execute(
            """
        CREATE TABLE IF NOT EXISTS leads (
            id TEXT PRIMARY KEY,
            address TEXT,
            city TEXT,
            price INTEGER,
            price_text TEXT,
            source TEXT,
            source_type TEXT,
            link TEXT,
            description TEXT,
            owner_name TEXT,
            owner_mailing TEXT,
            motivation TEXT,
            deal_score INTEGER,
            equity_estimate TEXT,
            status TEXT DEFAULT 'new',
            created_at TEXT,
            updated_at TEXT,
            raw_data TEXT
        )
        """
        )
        c.execute(
            """
        CREATE TABLE IF NOT EXISTS scrape_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            source_type TEXT,
            found INTEGER,
            new_leads INTEGER,
            error TEXT,
            created_at TEXT
        )
        """
        )
        # Migration: add source_type to scrape_log for pre-existing databases
        try:
            c.execute("ALTER TABLE scrape_log ADD COLUMN source_type TEXT")
        except sqlite3.OperationalError:
            pass  # column already exists
        c.execute(
            "CREATE TABLE IF NOT EXISTS last_run_summary ("
            "id INTEGER PRIMARY KEY CHECK (id = 1),"
            "started_at TEXT,"
            "finished_at TEXT,"
            "total_found INTEGER,"
            "total_new INTEGER,"
            "source_summary TEXT,"
            "error TEXT"
            ")"
        )


def upsert_lead(lead: dict) -> bool:
    conn = get_conn()
    try:
        with conn:
            return _upsert_lead(conn, lead)
    finally:
        conn.close()


def _upsert_lead(conn: sqlite3.Connection, lead: dict) -> bool:
    conn.execute("BEGIN IMMEDIATE")
    c = conn.cursor()
    c.execute("SELECT id FROM leads WHERE id=?", (lead["id"],))
    exists = c.fetchone()
    if exists:
        c.execute(
            """
        UPDATE leads SET address=:address, city=:city, price=:price,
            price_text=:price_text, source=:source, source_type=:source_type,
            link=:link, description=:description, owner_name=:owner_name,
            owner_mailing=:owner_mailing, motivation=:motivation,
            deal_score=:deal_score, equity_estimate=:equity_estimate,
            updated_at=:updated_at, raw_data=:raw_data
        WHERE id=:id
        """,
            lead,
        )
    else:
        c.execute(
            """
        INSERT INTO leads (id, address, city, price, price_text, source, source_type,
            link, description, owner_name, owner_mailing, motivation, deal_score,
            equity_estimate, status, created_at, updated_at, raw_data)
        VALUES (:id, :address, :city, :price, :price_text, :source, :source_type,
            :link, :description, :owner_name, :owner_mailing, :motivation, :deal_score,
            :equity_estimate, :status, :created_at, :updated_at, :raw_data)
        """,
            lead,
        )
    return exists is None


def get_leads(min_score: int = 0, city: str | None = None, limit: int = 100) -> list[sqlite3.Row]:
    with closing(get_conn()) as conn, conn:
        c = conn.cursor()
        query = "SELECT * FROM leads WHERE deal_score >= ?"
        params: list[Any] = [min_score]
        if city:
            query += " AND city LIKE ?"
            params.append(f"%{city}%")
        query += " ORDER BY deal_score DESC, created_at DESC LIMIT ?"
        params.append(limit)
        c.execute(query, params)
        return c.fetchall()


def get_stats() -> dict[str, Any]:
    with closing(get_conn()) as conn, conn:
        c = conn.cursor()
        stats: dict[str, Any] = {}
        c.execute("SELECT COUNT(*) FROM leads")
        stats["total"] = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM leads WHERE deal_score >= 7")
        stats["hot"] = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM leads WHERE deal_score >= 5")
        stats["warm"] = c.fetchone()[0]
        c.execute("SELECT source, COUNT(*) as cnt FROM leads GROUP BY source")
        stats["by_source"] = dict(c.fetchall())
        c.execute("SELECT city, COUNT(*) as cnt FROM leads GROUP BY city ORDER BY cnt DESC")
        stats["by_city"] = dict(c.fetchall())
        return stats


def get_recent_scrapes(limit: int = 20) -> list[sqlite3.Row]:
    conn = get_conn()
    try:
        return conn.execute(
            "SELECT * FROM scrape_log ORDER BY created_at DESC, id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    finally:
        conn.close()


def save_last_run_summary(
    source_summary: dict[str, dict[str, Any]],
    total_found: int,
    total_new: int,
    error: str | None = None,
) -> bool:
    conn = get_conn()
    try:
        with conn:
            c = conn.cursor()
            finished_at = datetime.now(timezone.utc).isoformat()
            c.execute(
                "INSERT OR REPLACE INTO last_run_summary "
                "(id, started_at, finished_at, total_found, total_new, source_summary, error) "
                "VALUES (1, 0, ?, ?, ?, ?, ?)",
                (finished_at, total_found, total_new, json.dumps(source_summary), error or ""),
            )
        return True
    except Exception:
        return False
    finally:
        conn.close()


def load_last_run_summary() -> dict[str, Any] | None:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM last_run_summary WHERE id = 1"
        ).fetchone()
        if not row:
            return None
        try:
            source_summary = json.loads(row["source_summary"]) if row["source_summary"] else {}
        except Exception:
            source_summary = {}
        return {
            "started_at": row["started_at"] or "",
            "finished_at": row["finished_at"],
            "total_found": row["total_found"],
            "total_new": row["total_new"],
            "source_summary": source_summary,
            "error": row["error"],
        }
    finally:
        conn.close()
