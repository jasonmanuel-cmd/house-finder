"""Tests for newspaper auction notice scraper — no live network or DB."""
import tempfile
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

import database
from scrapers import newspaper_auctions as na


def response(text='', status=200):
    r = Mock(status_code=status, text=text, content=text.encode(), headers={'Content-Type': 'text/html'})
    r.raise_for_status.side_effect = None if status == 200 else RuntimeError(f'HTTP {status}')
    return r


class NewspaperAuctionParsingTests(unittest.TestCase):
    def test_parses_apn_owner_amount_triples(self):
        html = """
        NOTICE OF PUBLIC AUCTION ON March 10, 2025
        The following is a partial list:
        031-330-08-00-6 $1,300.00
        TRAMPP JACK H & PHYLLIS J
        042-065-22-00-3 $700.00 S
        TRINGFELLOW DARLENE
        042-280-08-00-2 $3,900.00
        BLAKELY ANDREW G JR
        198-190-07-03-6 $700.00
        MC GEE FRANK E & ANNA L
        123 KERN ST TAFT
        (PUB: TMD, July 17, 24, 31, 2025)
        """
        leads = na.parse_notice_html(html, "taft_midway_driller")
        self.assertEqual(len(leads), 4)
        self.assertEqual(leads[0]["apn"], "031-330-08-00-6")
        self.assertEqual(leads[0]["owner_name"], "TRAMPP JACK H & PHYLLIS J")
        self.assertEqual(leads[0]["amount"], 1300)
        self.assertEqual(leads[1]["apn"], "042-065-22-00-3")
        self.assertEqual(leads[1]["owner_name"], "TRINGFELLOW DARLENE")
        self.assertEqual(leads[1]["amount"], 700)

    def test_infer_city_from_context(self):
        html = """
        NOTICE OF PUBLIC AUCTION
        212-452-12-00-5 $11,700.00
        NOSALA THOMAS M & EDNA V
        209 DESERT BREEZE DR CALIF CITY
        California City is in Kern County.
        """
        leads = na.parse_notice_html(html, "mojave_desert_news")
        self.assertTrue(leads)
        self.assertEqual(leads[0]["city"], "California City")

    def test_empty_html_returns_no_leads(self):
        self.assertEqual(na.parse_notice_html("", "source"), [])
        self.assertEqual(na.parse_notice_html("<html><body>No auction here</body></html>", "source"), [])

    def test_skip_rows_without_owner(self):
        html = "031-330-08-00-6 $1,300.00\n(PUB: TMD, July 17, 24, 31, 2025)"
        leads = na.parse_notice_html(html, "taft")
        self.assertEqual(leads, [])

    def test_duplicate_apn_deduplicated(self):
        html = """
        031-330-08-00-6 $1,300.00
        TRAMPP JACK H & PHYLLIS J
        031-330-08-00-6 $1,300.00
        TRAMPP JACK H & PHYLLIS J
        """
        leads = na.parse_notice_html(html, "taft")
        self.assertEqual(len(leads), 1)


class NewspaperAuctionFetchTests(unittest.TestCase):
    def test_no_leads_is_reported_as_error(self):
        with patch("database.upsert_lead") as save:
            with patch.object(na.requests, "get", return_value=response("<html>nothing</html>")):
                found, new, errors = na.scrape_newspaper_auctions(
                    urls=["https://example.com/empty.html"]
                )
                self.assertEqual((found, new), (0, 0))
                self.assertIn("empty or too short", errors)
                save.assert_not_called()

    def test_html_without_rows_is_reported_as_error(self):
        html = "<html><body>" + ("<p>Lorem ipsum dolor sit amet</p>" * 20) + "</body></html>"
        with patch("database.upsert_lead") as save:
            with patch.object(na.requests, "get", return_value=response(html)):
                found, new, errors = na.scrape_newspaper_auctions(
                    urls=["https://example.com/no_rows.html"]
                )
                self.assertEqual((found, new), (0, 0))
                self.assertIn("no verified APN-owner", errors)
                save.assert_not_called()

    def test_404_is_reported_without_retry(self):
        with patch("database.upsert_lead") as save:
            with patch.object(na.requests, "get", return_value=response("", 404)):
                found, new, errors = na.scrape_newspaper_auctions(
                    urls=["https://example.com/missing.html"]
                )
                self.assertIn("HTTP 404", errors)
                save.assert_not_called()

    def test_verified_rows_are_persisted(self):
        html = """
        NOTICE OF PUBLIC AUCTION ON March 10, 2025
        The following is a partial list:
        031-330-08-00-6 $1,300.00
        TRAMPP JACK H & PHYLLIS J
        042-065-22-00-3 $700.00
        TRINGFELLOW DARLENE
        """
        with tempfile.TemporaryDirectory() as temp:
            db_path = os.path.join(temp, "test.db")
            with patch.object(database, "DB_PATH", db_path):
                database.init_db()
                with patch.object(na.requests, "get", return_value=response(html)):
                    found, new, errors = na.scrape_newspaper_auctions(
                        urls=["https://example.com/notice.html"]
                    )
                    self.assertEqual(found, 2)
                    self.assertEqual(new, 2)
                    conn = database.get_conn()
                    rows = conn.execute("SELECT * FROM leads").fetchall()
                    conn.close()
                    self.assertEqual(len(rows), 2)
                    self.assertEqual(rows[0]["source"], "newspaper_auction")
                    self.assertEqual(rows[0]["owner_name"], "TRAMPP JACK H & PHYLLIS J")


if __name__ == "__main__":
    unittest.main()
