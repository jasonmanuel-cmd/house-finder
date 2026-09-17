"""Persistence regressions; each test uses an isolated, real SQLite database."""
import os
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from unittest.mock import patch

import database


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "nested" / "leads.db"
        self.db_patch = patch.object(database, "DB_PATH", str(self.path))
        self.db_patch.start()
        self.addCleanup(self.db_patch.stop)
        database.init_db()

    def lead(self, **changes):
        lead = dict(id="one", address="Old address", city="Old city", price=100,
                    price_text="$100", source="old", source_type="fsbo",
                    link="https://old.example", description="old description",
                    owner_name="Old owner", owner_mailing="Old mailing",
                    motivation="old motivation", deal_score=9,
                    equity_estimate="old equity", status="new",
                    created_at="2026-01-01", updated_at="2026-01-01",
                    raw_data="old raw")
        lead.update(changes)
        return lead

    def test_rescrape_refreshes_fields_preserves_workflow_and_creation(self):
        original = self.lead()
        self.assertIs(database.upsert_lead(original), True)
        conn = database.get_conn()
        try:
            conn.execute("UPDATE leads SET status='contacted' WHERE id='one'")
            conn.commit()
        finally:
            conn.close()
        refreshed = {key: "changed " + key for key in original}
        refreshed.update(id="one", price=50, deal_score=2, status="new")
        self.assertIs(database.upsert_lead(refreshed), False)
        actual = dict(database.get_leads()[0])
        expected = dict(refreshed, status="contacted", created_at=original['created_at'])
        self.assertEqual(actual, expected)
        self.assertEqual(original, self.lead(), "input must not be mutated")

    def test_relative_filename_initializes_in_current_directory(self):
        previous = os.getcwd()
        try:
            os.chdir(self.temp.name)
            with patch.object(database, "DB_PATH", "relative.db"):
                database.init_db()
                self.assertTrue(database.upsert_lead(self.lead()))
                self.assertEqual(len(database.get_leads()), 1)
        finally:
            os.chdir(previous)

    def test_recent_scrapes_are_newest_first_and_limited(self):
        self.assertEqual(database.get_recent_scrapes(), [])
        conn = database.get_conn()
        try:
            with conn:
                conn.executemany(
                    "INSERT INTO scrape_log (source, found, new_leads, error, created_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    [("latest", 3, 1, None, "2026-03-01"),
                     ("old", 0, 0, "network error", "2026-01-01"),
                     ("tie", 1, 0, None, "2026-03-01")])
        finally:
            conn.close()
        rows = database.get_recent_scrapes(limit=2)
        self.assertEqual([row['source'] for row in rows], ['tie', 'latest'])
        self.assertEqual(rows[1]['new_leads'], 1)
        self.assertEqual(database.get_recent_scrapes(limit=0), [])

    def test_failed_write_releases_lock_and_leaves_existing_lead_intact(self):
        database.upsert_lead(self.lead())
        invalid = self.lead(price=object())
        with self.assertRaises(sqlite3.Error):
            database.upsert_lead(invalid)
        self.assertEqual(database.get_leads()[0]['price'], 100)
        self.assertFalse(database.upsert_lead(self.lead(price=200)))
        self.assertEqual(database.get_leads()[0]['price'], 200)

    def test_existing_schema_filters_stats_and_repeated_init(self):
        database.upsert_lead(self.lead())
        database.upsert_lead(self.lead(id='two', city='Bakersfield', deal_score=5))
        database.upsert_lead(self.lead(id='three', city='Bakersfield', deal_score=1))
        database.init_db()
        self.assertEqual(len(database.get_leads(min_score=5, city='Bakers', limit=1)), 1)
        self.assertEqual(database.get_stats(), {
            'total': 3, 'hot': 1, 'warm': 2,
            'by_source': {'old': 3}, 'by_city': {'Bakersfield': 2, 'Old city': 1}})

    def test_concurrent_upserts_count_exactly_one_new_lead(self):
        workers = 16
        barrier = Barrier(workers)

        def save(index):
            barrier.wait(timeout=10)
            return database.upsert_lead(self.lead(price=index))

        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(save, range(workers)))
        self.assertEqual(sum(results), 1)
        self.assertEqual(len(database.get_leads()), 1)


if __name__ == "__main__":
    unittest.main()
