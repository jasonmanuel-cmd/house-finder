"""Synthetic fixtures only: no test fixture represents a real property."""
import unittest
from unittest.mock import patch, Mock
from scrapers import kern_tax, bakersfield_code, zillow_fsbo


def response(text='', status=200):
    r = Mock(status_code=status, text=text, content=text.encode(), headers={'Content-Type': 'text/html'})
    r.raise_for_status.side_effect = None if status == 200 else RuntimeError(f'HTTP {status}')
    return r


class ScraperTests(unittest.TestCase):
    def test_resource_pages_never_become_leads(self):
        for module, function in [(kern_tax, kern_tax.scrape_kern_tax),
                                 (bakersfield_code, bakersfield_code.scrape_bakersfield_code),
                                 (zillow_fsbo, zillow_fsbo.scrape_zillow_fsbo)]:
            with self.subTest(module=module.__name__), patch.object(module.requests, 'get', return_value=response('<a href="guide.pdf">Guide</a>')), patch.object(module, 'upsert_lead') as save:
                result = function()
                self.assertEqual(result[:2], (0, 0))
                self.assertTrue(result[2], 'Unsupported parsing must be reported')
                save.assert_not_called()


class ZillowParsingTests(unittest.TestCase):
    def test_structured_prices_stay_with_their_properties(self):
        import json
        # Explicitly synthetic Zillow-shaped fixture, not a live capture.
        listings = [
            {'zpid': 'synthetic1', 'addressStreet': '1 Synthetic St', 'addressCity': 'Fixture City', 'unformattedPrice': 123000, 'detailUrl': '/homedetails/synthetic1_zpid/', 'listingSubType': {'is_FSBO': True}},
            {'zpid': 'synthetic2', 'addressStreet': '2 Synthetic St', 'addressCity': 'Fixture City', 'unformattedPrice': 456000, 'detailUrl': '/homedetails/synthetic2_zpid/', 'listingSubType': {'is_FSBO': True}},
            {'zpid': 'agent', 'addressStreet': '3 Synthetic St', 'listingSubType': {'is_FSBO': False}},
        ]
        data = {'props': {'pageProps': {'searchPageState': {'cat1': {'searchResults': {'listResults': listings}}}}}}
        html = '<script id="__NEXT_DATA__" type="application/json">' + json.dumps(data) + '</script>'
        with patch.object(zillow_fsbo, 'ZILLOW_FSBO_URLS', ['https://www.zillow.com/test']), patch.object(zillow_fsbo.requests, 'get', return_value=response(html)), patch.object(zillow_fsbo, 'upsert_lead', side_effect=[True, False]) as save:
            self.assertEqual(zillow_fsbo.scrape_zillow_fsbo(), (2, 1, ''))
            self.assertEqual([c.args[0]['price'] for c in save.call_args_list], [123000, 456000])
            self.assertEqual(save.call_args_list[0].args[0]['address'], '1 Synthetic St')


class CraigslistTests(unittest.TestCase):
    def test_html_block_is_not_empty_success(self):
        from scrapers import craigslist
        with patch('requests.get', return_value=response('<html>blocked</html>', 403)), patch.object(craigslist, 'CRAIGSLIST_RSS', ['https://bakersfield.craigslist.org/search/reo?format=rss']), patch.object(craigslist, 'upsert_lead') as save, patch.object(craigslist.feedparser, 'parse', return_value=Mock(entries=[])):
            found, new, error = craigslist.scrape_craigslist()
            self.assertEqual((found, new), (0, 0))
            self.assertIn('403', error)
            save.assert_not_called()

    def test_html_200_is_reported_as_parse_failure(self):
        from scrapers import craigslist
        with patch('requests.get', return_value=response('<html>Access denied</html>')), patch.object(craigslist, 'CRAIGSLIST_RSS', ['https://bakersfield.craigslist.org/search/reo']), patch.object(craigslist, 'upsert_lead') as save:
            found, new, errors = craigslist.scrape_craigslist()
            self.assertEqual((found, new), (0, 0))
            self.assertIn('Invalid RSS', errors)
            save.assert_not_called()

    def test_valid_empty_feed_is_success(self):
        from scrapers import craigslist
        xml = '<rss version="2.0"><channel><title>Synthetic empty fixture</title><link>https://bakersfield.craigslist.org</link><description>Test</description></channel></rss>'
        with patch('requests.get', return_value=response(xml)), patch.object(craigslist, 'CRAIGSLIST_RSS', ['https://bakersfield.craigslist.org/search/reo']):
            self.assertEqual(craigslist.scrape_craigslist(), (0, 0, ''))

    def test_synthetic_rss_duplicate_and_unknown_city(self):
        from scrapers import craigslist
        xml = '''<rss version="2.0"><channel><title>Synthetic tests</title><link>https://bakersfield.craigslist.org</link><description>Fixture</description><item><title>$123,000 Synthetic parcel</title><link>https://bakersfield.craigslist.org/reo/d/synthetic/1234567890.html</link><guid>synthetic-id</guid><description>Synthetic fixture only</description></item></channel></rss>'''
        with patch('requests.get', return_value=response(xml)), patch.object(craigslist, 'CRAIGSLIST_RSS', ['https://bakersfield.craigslist.org/search/reo?query=Tehachapi', 'https://bakersfield.craigslist.org/search/reo']), patch.object(craigslist, 'upsert_lead', return_value=True) as save:
            self.assertEqual(craigslist.scrape_craigslist(), (1, 1, ''))
            self.assertEqual(save.call_args.args[0]['city'], '')
            self.assertEqual(save.call_args.args[0]['price'], 123000)


class OrchestratorTests(unittest.TestCase):
    def test_results_and_logs_include_failed_source(self):
        import tempfile
        import os
        import database
        import run
        with tempfile.TemporaryDirectory() as temp,           patch.object(database, 'DB_PATH', os.path.join(temp, 'synthetic.db')),           patch.object(run, 'scrape_craigslist', return_value=(2, 1, 'partial')),           patch.object(run, 'scrape_zillow_fsbo', side_effect=RuntimeError('synthetic failure')),           patch.object(run, 'scrape_kern_tax', return_value=(0, 0, 'unsupported')),           patch.object(run, 'scrape_bakersfield_code', return_value=(0, 0, 'unsupported')),           patch.object(run, 'scrape_browser_sources', return_value=(0, 0, 'skipped_browser')), patch.object(run, 'scrape_kern_code_cases', create=True, return_value=(3, 3, 'Partial coverage')), patch.object(run, 'scrape_newspaper_auctions', create=True, return_value=(3, 3, 'Partial coverage')):
            result = run.run_all()
            conn = database.get_conn()
            try:
                rows = conn.execute('SELECT source, found, new_leads, error FROM scrape_log').fetchall()
            finally:
                conn.close()
            self.assertEqual(len(rows), 7)
            self.assertEqual(result['kern_code_cases']['new'], 3)
            self.assertEqual(result['newspaper_auctions']['new'], 3)
            self.assertEqual(result['craigslist']['new'], 1)
            self.assertIn('synthetic failure', result['zillow_fsbo']['errors'])
            self.assertEqual(dict((row['source'], row['found']) for row in rows)['craigslist'], 2)


if __name__ == '__main__':
    unittest.main()
