"""Offline browser quality regressions; never visit sites or use the live DB."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import MagicMock, patch

if importlib.util.find_spec("playwright") is None:
    optional = types.ModuleType("playwright.sync_api")
    optional.Page = object
    optional.Browser = object
    optional.sync_playwright = MagicMock()
    with patch.dict(sys.modules, {"playwright": types.ModuleType("playwright"),
                                  "playwright.sync_api": optional}):
        from scrapers import browser_source as browser
else:
    from scrapers import browser_source as browser


class FakePage:
    def __init__(self, html=None, status=200, title="Public records"):
        self.html = html or "<html><body>Office: 1115 Truxtun Avenue. Example APN 123-456-789-00-1.</body></html>"
        self.status = status
        self.page_title = title
        self.url = "https://example.gov/records"
        self.visits = []
        self.closed = False

    def goto(self, url, **kwargs):
        self.url = url
        self.visits.append(url)
        return types.SimpleNamespace(status=self.status)

    def content(self):
        return self.html

    def title(self):
        return self.page_title

    def eval_on_selector_all(self, selector, script):
        return [{"text": "Permit search", "href": "https://example.gov/permits"},
                {"text": "Contact", "href": "https://example.gov/contact"}]

    def close(self):
        self.closed = True


class BrowserQualityTests(unittest.TestCase):
    def test_challenge_beyond_snapshot_preview_is_still_detected(self):
        html = '<html><head>' + (' ' * 13000) + '</head><body>Verify you are human</body></html>'
        snap = browser.snapshot_page(FakePage(html), "https://example.gov/records")
        self.assertFalse(browser.is_likely_public_surface(snap))
        self.assertLessEqual(len(snap["text_head"]), 12000)

    def test_browser_launch_does_not_hide_automation_or_spoof_default_user_agent(self):
        manager = MagicMock()
        with patch.object(browser, "sync_playwright", return_value=manager):
            driver, page, context = browser.build_browser_launch()
        chromium = manager.__enter__.return_value.chromium
        chromium.launch.assert_called_once_with(headless=True)
        self.assertNotIn("user_agent", driver.new_context.call_args.kwargs)
        self.assertIs(context, manager)
        self.assertIs(page, driver.new_context.return_value.new_page.return_value)

    def test_blocked_and_challenge_surfaces_are_errors_not_candidates(self):
        cases = [(403, "Forbidden"), (429, "Too many requests"), (500, "Server error"),
                 (302, "Redirect"), (304, "Not modified"), (None, "No response"),
                 (200, "Just a moment..."), (200, "Verify you are human"),
                 (200, "Access denied"), (200, "Sign in to continue")]
        for status, title in cases:
            with self.subTest(status=status, title=title), tempfile.TemporaryDirectory() as temp:
                page = FakePage(status=status, title=title)
                source = browser.SourceSpec("blocked", title, page.url, "assessor")
                with patch.object(browser, "ARTIFACT_DIR", Path(temp)), \
                        patch.object(browser, "SOURCES", [source]), \
                        patch.object(browser, "build_browser", return_value=(MagicMock(), page, MagicMock())), \
                        patch("database.upsert_lead") as save:
                    found, new, errors = browser.scrape_browser_sources()
                    self.assertEqual((found, new), (0, 0))
                    self.assertTrue(errors, "Blocked/inaccessible pages must not report success")
                    save.assert_not_called()
                    item = json.loads(next(Path(temp).glob("*.json")).read_text(encoding="utf-8"))["sources"][0]
                    self.assertEqual(item["status"], status)
                    self.assertFalse(item["reachable"])
                    self.assertEqual(item["candidate_links"], [])
                    self.assertTrue(item["error"])
                    self.assertEqual(page.visits, [source.start_url])

    def test_investigation_is_saved_as_artifact_never_as_a_lead(self):
        page, driver, context = FakePage(), MagicMock(), MagicMock()
        source = browser.SourceSpec("generic", "Public records", page.url, "assessor")
        with tempfile.TemporaryDirectory() as temp, \
                patch.object(browser, "ARTIFACT_DIR", Path(temp), create=True), \
                patch.object(browser, "SOURCES", [source]), \
                patch.object(browser, "build_browser", return_value=(driver, page, context)), \
                patch("database.upsert_lead") as save:
            self.assertEqual(browser.scrape_browser_sources(), (0, 0, ""))
            save.assert_not_called()
            files = list(Path(temp).glob("*.json"))
            self.assertEqual(len(files), 1)
            report = json.loads(files[0].read_text(encoding="utf-8"))
            item = report["sources"][0]
            self.assertEqual(item["source_key"], source.key)
            self.assertEqual(item["status"], 200)
            self.assertEqual(item["candidate_links"][0]["href"], "https://example.gov/permits")
            self.assertEqual(item["leads_extracted"], 0)
            self.assertNotIn("id", item)
            self.assertEqual(page.visits, [source.start_url])
            self.assertTrue(page.closed)
            driver.close.assert_called_once()
            context.__exit__.assert_called_once()

    def test_auction_browser_path_is_retired_without_duplicate_or_lossy_records(self):
        page = FakePage('<html><a href="/ca/cakern/1348/openstandardparcel/99/123-456-789-00-1">'
                        '123-456-789-00-1</a>Minimum Bid $2,345.67 Year 2026 ZIP 93301</html>')
        self.assertEqual(browser.parse_govease_auction(page, "govease_kern_auction", "1348"), [])
        self.assertNotIn("govease_kern_auction", [s.key for s in browser.SOURCES])

    def test_generic_office_addresses_and_sample_parcels_are_not_leads(self):
        page = FakePage()
        for parser in (browser.parse_bakersfield_building_permits,
                       browser.parse_kern_assessor_recorder):
            with self.subTest(parser=parser.__name__):
                self.assertEqual(parser(page, "generic"), [])


if __name__ == "__main__":
    unittest.main()
