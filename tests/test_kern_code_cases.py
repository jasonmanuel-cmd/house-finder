"""Tests use captured live Kern public enforcement results, not invented leads."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'artifacts/nonauction-probes/accela_search.html'

class KernCodeCasesTests(unittest.TestCase):
    def test_record_links_must_stay_on_kern_public_enforcement_details(self):
        from bs4 import BeautifulSoup
        from scrapers.kern_code_cases import parse_cases
        for href in ['javascript:alert(1)', 'https://example.com/record', '/KERNCO/Cap/CapDetail.aspx?Module=Building']:
            soup = BeautifulSoup(FIXTURE.read_text(encoding='utf8'), 'html.parser')
            soup.select_one('a[id$=hlPermitNumber]')['href'] = href
            with self.subTest(href=href), self.assertRaisesRegex(ValueError, 'record link'):
                parse_cases(str(soup))

    def test_duplicate_rows_do_not_duplicate_case_identity(self):
        from bs4 import BeautifulSoup
        from scrapers.kern_code_cases import parse_cases
        soup = BeautifulSoup(FIXTURE.read_text(encoding='utf8'), 'html.parser')
        baseline = len(parse_cases(str(soup)))
        self.assertGreaterEqual(baseline, 1)
        row = soup.select_one('a[id$=hlPermitNumber]').find_parent('tr')
        from copy import copy
        row.insert_after(copy(row))
        self.assertEqual(len(parse_cases(str(soup))), baseline)

    def test_only_addressed_pending_enforcement_cases_are_leads(self):
        from bs4 import BeautifulSoup
        from scrapers.kern_code_cases import parse_cases
        baseline = parse_cases(FIXTURE.read_text(encoding='utf8'))
        self.assertGreaterEqual(len(baseline), 1)
        first_id = baseline[0]['id']
        for suffix, replacement in [('lblType', 'Building Permit'), ('lblStatus', 'Closed'),
                                     ('lblPermitAddress', ''), ('lblPermitAddress', 'No address')]:
            soup = BeautifulSoup(FIXTURE.read_text(encoding='utf8'), 'html.parser')
            # modify the field inside the first row that currently yields a lead
            target_row = None
            for anchor in soup.select('a[id$=hlPermitNumber]'):
                row = anchor.find_parent('tr')
                if row and f"kern_code_{anchor.get_text(' ', strip=True)}" == first_id:
                    target_row = row
                    break
            self.assertIsNotNone(target_row, 'fixture row for first lead not found')
            target_row.select_one(f'[id$={suffix}]').string = replacement
            with self.subTest(field=suffix, value=replacement):
                leads = parse_cases(str(soup))
                self.assertEqual(len(leads), len(baseline) - 1)
                self.assertNotIn(first_id, [lead['id'] for lead in leads])

    def test_non_results_html_is_failure_not_empty_success(self):
        from scrapers.kern_code_cases import parse_cases
        for text in ['<html>Access denied</html>', '<html>Login required</html>',
                     '<html>An error has occurred</html>', '<html>Search for Records</html>']:
            with self.subTest(text=text), self.assertRaisesRegex(ValueError, 'results'):
                parse_cases(text)

    def test_live_case_rows_preserve_unverified_status_without_distress_score(self):
        self.assertIsNotNone(importlib.util.find_spec('scrapers.kern_code_cases'),
                             'Verified Kern public code-case adapter is missing')
        from scrapers.kern_code_cases import parse_cases
        leads = parse_cases(FIXTURE.read_text(encoding='utf8'))
        self.assertGreaterEqual(len(leads), 1)
        lead = leads[0]
        self.assertRegex(lead['id'], r'^kern_code_C\d+$')
        self.assertTrue(lead['address'])
        self.assertTrue(lead['city'])
        self.assertEqual(lead['source_type'], 'code_case')
        self.assertEqual(lead['deal_score'], 0)
        self.assertEqual(lead['motivation'], 'unknown')
        self.assertIn('Pending Initial Inspection', lead['description'])
        self.assertIn('capID3=', lead['link'])
        self.assertEqual(lead['owner_name'], '')
        self.assertEqual(lead['price'], 0)

class PublicSession:
    """Transport double; real public HTML still exercises form and row parsing."""
    def __init__(self):
        self.posts = []

    def get(self, url, **kwargs):
        return self.response((FIXTURE.parent / 'accela.html').read_text(encoding='utf8'))

    def post(self, url, **kwargs):
        self.posts.append(kwargs)
        return self.response(FIXTURE.read_text(encoding='utf8'))

    @staticmethod
    def response(text):
        from requests import Response
        response = Response()
        response.status_code = 200
        response._content = text.encode('utf8')
        response.encoding = 'utf8'
        return response


class KernCodeFetchTests(unittest.TestCase):
    def test_missing_public_search_form_stops_before_post(self):
        import scrapers.kern_code_cases as module
        session = PublicSession()
        session.get = lambda *args, **kwargs: session.response('<html>Login required</html>')
        saved = []
        result = module.scrape_kern_code_cases(session=session, save=lambda lead: saved.append(lead))
        self.assertEqual(result[:2], (0, 0))
        self.assertIn('form', result[2].lower())
        self.assertFalse(session.posts)
        self.assertFalse(saved)

    def test_public_search_ingests_cases_and_reports_first_page_limit(self):
        import scrapers.kern_code_cases as module
        self.assertTrue(callable(getattr(module, 'scrape_kern_code_cases', None)),
                        'Public form fetch adapter is missing')
        session = PublicSession()
        saved = []
        result = module.scrape_kern_code_cases(session=session, save=lambda lead: saved.append(lead) or True,
                                              start_date='09/01/2026', end_date='09/16/2026')
        self.assertGreaterEqual(result[0], 1)
        self.assertEqual(result[1], len(saved))
        self.assertEqual(result[0], result[1])
        self.assertGreaterEqual(len(saved), 1)
        self.assertIn('partial', result[2].lower())
        post = session.posts[0]
        self.assertEqual(post['data']['__EVENTTARGET'], 'ctl00$PlaceHolderMain$btnNewSearch')
        self.assertEqual(post['data']['ctl00$PlaceHolderMain$generalSearchForm$txtGSStartDate'], '09/01/2026')
        self.assertTrue(post['data']['__VIEWSTATE'])
        self.assertEqual(post['headers']['Origin'], 'https://aca-prod.accela.com')


if __name__ == '__main__':
    unittest.main()
