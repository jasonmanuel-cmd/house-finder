"""Real Kern County tax auction ingestion tests — synthetic fixtures only."""
import json
import unittest
from unittest.mock import patch, Mock

from scrapers import kern_tax


def _response(text="", status=200):
    r = Mock(status_code=status, text=text, content=text.encode(), headers={"Content-Type": "text/html"})
    r.raise_for_status.side_effect = None if status == 200 else RuntimeError(f"HTTP {status}")
    return r


class KernAuctionDiscoveryTests(unittest.TestCase):
    def test_discovery_fails_gracefully_when_general_page_unavailable(self):
        with patch.object(kern_tax, "_discover_current_auction", return_value={}):
            found, new, errors = kern_tax.scrape_kern_tax()
        self.assertEqual((found, new), (0, 0))
        self.assertTrue(errors)

    def test_discovered_auction_url_is_used_when_general_page_reachable(self):
        with patch.object(kern_tax, "_discover_current_auction", return_value={"auction_id": "1348", "browse_url": "https://liveauctions.govease.com/ca/cakern/1348/browsestandard"}), \
             patch.object(kern_tax.requests, "get", return_value=_response("<html></html>", 200)), \
             patch.object(kern_tax, "_parse_standard_browse_page", side_effect=NotImplementedError("synthetic readback only")):
            found, new, errors = kern_tax.scrape_kern_tax()
        self.assertEqual((found, new), (0, 0))
        self.assertIn("1348", errors)


class KernAuctionParsingTests(unittest.TestCase):
    def test_non_parcel_rows_and_non_numeric_bids_are_rejected(self):
        html = """
        <table>
          <thead><tr><th>Unique #</th><th>Parcel #</th><th>Owner Name</th><th>Minimum Bid</th></tr></thead>
          <tbody>
            <tr><td>1</td><td>019-222-17-00-4</td><td>SMITH JOHN</td><td>$18,800.00</td></tr>
            <tr><td>2</td><td>020-000-00-00-0</td><td>VACANT LOT</td><td></td></tr>
            <tr><td>3</td><td>031-040-01-00-1</td><td>HAAS KENNETH N</td><td>Starting bid</td></tr>
            <tr><td>4</td><td>031-050-19-00-7</td><td>HAAS KENNETH N</td><td>$11,700.00</td></tr>
            <tr><td>5</td><td>031-430-18-00-4</td><td>CARDENA RAFAEL &amp; BAL...</td><td>$1,800.00</td></tr>
            <tr><td>6</td><td>031-460-21-00-1</td><td>PATEL JAGDISHBHAI N ...</td><td>$109,500.00</td></tr>
            <tr><td>7</td><td>039-051-20-00-2</td><td>SALAZAR JOE &amp; SUSAN ...</td><td>$32,900.00</td></tr>
            <tr><td>8</td><td>039-272-09-00-2</td><td>WOLFE WESLEY THOMAS</td><td>$32,600.00</td></tr>
            <tr><td>9</td><td>039-363-04-00-0</td><td>INIGUEZ RICARDO &amp; LA...</td><td>$20,300.00</td></tr>
            <tr><td>10</td><td>042-202-06-00-6</td><td>MADSEN MARK</td><td>$16,400.00</td></tr>
          </tbody>
        </table>
        """
        with patch.object(kern_tax, "_discover_current_auction", return_value={"auction_id": "1348", "browse_url": "https://liveauctions.govease.com/ca/cakern/1348/browsestandard"}), \
             patch.object(kern_tax.requests, "get", return_value=_response(html, 200)), \
             patch.object(kern_tax, "upsert_lead", return_value=True) as save:
            found, new, errors = kern_tax.scrape_kern_tax()
        # Valid parcels: rows 1,4,5,6,7,8,9,10 — row 2 missing bid, row 3 non-numeric bid.
        self.assertEqual(found, 8)
        self.assertEqual(new, 8)
        self.assertFalse(errors)
        args = [c.args[0] for c in save.call_args_list]
        self.assertEqual(args[0]["address"], "APN 019-222-17-00-4")
        self.assertEqual(args[0]["price"], 0)
        self.assertEqual(args[0]["price_text"], "Minimum bid $18,800.00")
        self.assertEqual(args[1]["address"], "APN 042-202-06-00-6")
        self.assertEqual(args[1]["price"], 16400)
        self.assertEqual(args[1]["price_text"], "$16,400")
        self.assertEqual(len(args), 8)
        self.assertNotIn("Starting bid", "\n".join(c.args[0]["price_text"] for c in save.call_args_list))

    def test_exact_synthetic_counts_from_visible_page(self):
        html = """
        <table>
          <thead><tr><th>Unique #</th><th>Parcel #</th><th>Owner Name</th><th>Minimum Bid</th></tr></thead>
          <tbody>
            <tr><td>1</td><td>019-222-17-00-4</td><td>SMITH JOHN</td><td>$18,800.00</td></tr>
            <tr><td>2</td><td>020-000-00-00-0</td><td>VACANT LOT</td><td></td></tr>
            <tr><td>3</td><td>031-040-01-00-1</td><td>HAAS KENNETH N</td><td>Starting bid</td></tr>
            <tr><td>4</td><td>031-050-19-00-7</td><td>HAAS KENNETH N</td><td>$11,700.00</td></tr>
            <tr><td>5</td><td>031-430-18-00-4</td><td>CARDENA RAFAEL &amp; BAL...</td><td>$1,800.00</td></tr>
            <tr><td>6</td><td>031-460-21-00-1</td><td>PATEL JAGDISHBHAI N ...</td><td>$109,500.00</td></tr>
            <tr><td>7</td><td>039-051-20-00-2</td><td>SALAZAR JOE &amp; SUSAN ...</td><td>$32,900.00</td></tr>
            <tr><td>8</td><td>039-272-09-00-2</td><td>WOLFE WESLEY THOMAS</td><td>$32,600.00</td></tr>
            <tr><td>9</td><td>039-363-04-00-0</td><td>INIGUEZ RICARDO &amp; LA...</td><td>$20,300.00</td></tr>
            <tr><td>10</td><td>042-202-06-00-6</td><td>MADSEN MARK</td><td>$16,400.00</td></tr>
          </tbody>
        </table>
        """
        with patch.object(kern_tax, "_discover_current_auction", return_value={"auction_id": "1348", "browse_url": "https://liveauctions.govease.com/ca/cakern/1348/browsestandard"}), \
             patch.object(kern_tax.requests, "get", return_value=_response(html, 200)), \
             patch.object(kern_tax, "upsert_lead", return_value=True):
            found, new, errors = kern_tax.scrape_kern_tax()
        self.assertEqual(found, 8)
        self.assertEqual(new, 8)
        self.assertFalse(errors)


class KernAuctionNoLeadsOnErrorsTests(unittest.TestCase):
    def test_networkfailure_produces_no_leads(self):
        with patch.object(kern_tax, "_discover_current_auction", return_value={}), \
             patch.object(kern_tax.requests, "get", side_effect=ConnectionError("synthetic")):
            found, new, errors = kern_tax.scrape_kern_tax()
        self.assertEqual((found, new), (0, 0))
        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
