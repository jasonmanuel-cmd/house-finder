"""Dashboard regression tests use an isolated temporary database."""
import tempfile
import os
import unittest
from pathlib import Path
from unittest.mock import patch
import database
from app import app


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_patch = patch.object(database, 'DB_PATH', str(Path(self.tmp.name) / 'leads.db'))
        self.db_patch.start()
        self.env_patch = patch.dict(os.environ, {'DASHBOARD_TOKEN': '', 'RENDER': ''})
        self.env_patch.start()
        app.config.update(TESTING=True, SECRET_KEY='test-session-key')
        self.client = app.test_client()
        with self.client.session_transaction() as sess:
            sess['csrf_token'] = 'test-csrf'
        self.client.environ_base['HTTP_X_CSRF_TOKEN'] = 'test-csrf'

    def tearDown(self):
        self.env_patch.stop()
        self.db_patch.stop()
        self.tmp.cleanup()

    def test_direct_export_initializes_fresh_database(self):
        self.assertEqual(self.client.get('/export').status_code, 200)

    def post_lead(self, **changes):
        data = dict(address='123 Main / Apt 2', city='Bakersfield', price='100000',
                    source='other', description='Owner submitted', link='https://example.com/listing')
        data.update(changes)
        return self.client.post('/add', data=data)

    def test_manual_validation_and_safe_id(self):
        for field in ('address', 'city', 'description', 'source'):
            with self.subTest(field=field):
                self.assertEqual(self.post_lead(**{field: '  '}).status_code, 400)
        for price in ('bad', '-1', '1.2', 'NaN', '999999999999999999999999'):
            with self.subTest(price=price):
                self.assertEqual(self.post_lead(price=price).status_code, 400)
        for link in ('javascript:alert(1)', '//evil.example', 'https://', 'data:text/html,test'):
            with self.subTest(link=link):
                self.assertEqual(self.post_lead(link=link).status_code, 400)
        self.assertEqual(self.post_lead().status_code, 302)
        conn = database.get_conn()
        rows = conn.execute('SELECT * FROM leads').fetchall()
        conn.close()
        self.assertEqual(len(rows), 1)
        self.assertRegex(rows[0]['id'], r'^manual_[a-f0-9]{32}$')
        self.assertEqual(self.client.post('/mark_contacted/' + rows[0]['id']).status_code, 200)

    def test_missing_contact_returns_404(self):
        self.assertEqual(self.client.post('/mark_contacted/missing').status_code, 404)

    def test_stored_xss_is_not_executable(self):
        self.post_lead(address='<script>alert(1)</script>')
        conn = database.get_conn()
        conn.execute("UPDATE leads SET id=?, link=?", ("x');alert(1);//", 'javascript:alert(2)'))
        conn.commit()
        conn.close()
        html = self.client.get('/').get_data(as_text=True)
        self.assertNotIn('href="javascript:', html)
        self.assertNotIn('onclick=', html)
        self.assertNotIn('<script>alert(1)</script>', html)
        self.assertIn('data-lead-id=', html)
        self.assertIn('encodeURIComponent', html)
        self.assertIn('response.ok', html)

    def test_csv_neutralizes_formula_cells(self):
        import csv
        import io
        for value in ('=1+1', '+SUM(A1)', '-1+1', '@SUM(A1)', '\t=1', '\r=2', '  =3'):
            self.post_lead(address=value)
        rows = list(csv.DictReader(io.StringIO(self.client.get('/export').get_data(as_text=True))))
        self.assertEqual(len(rows), 7)
        self.assertTrue(all(row['address'].startswith("'") for row in rows))

    def test_authentication_and_cloud_fail_closed(self):
        with patch.dict(os.environ, {'RENDER': 'true'}):
            self.assertEqual(self.client.get('/').status_code, 503)
            self.assertEqual(self.client.get('/export').status_code, 503)
        with patch.dict(os.environ, {'DASHBOARD_TOKEN': 'test-only-password'}):
            for path in ('/', '/export', '/scrape-status'):
                self.assertEqual(self.client.get(path).status_code, 401)
            self.assertEqual(self.client.get('/', auth=('admin', 'wrong')).status_code, 401)
            self.assertEqual(self.client.get('/', auth=('admin', 'test-only-password')).status_code, 200)
        self.assertEqual(self.client.get('/', base_url='http://evil.example').status_code, 403)

    def test_csrf_guards_mutations(self):
        for path in ('/add', '/mark_contacted/missing', '/run'):
            with self.subTest(path=path):
                self.assertEqual(self.client.post(path, headers={'X-CSRF-Token': ''}).status_code, 403)
                self.assertEqual(self.client.post(path, headers={'Origin': 'https://evil.example'}).status_code, 403)
                self.assertEqual(self.client.post(path, headers={'Sec-Fetch-Site': 'cross-site'}).status_code, 403)
        html = self.client.get('/').get_data(as_text=True)
        self.assertIn('name="csrf_token"', html)
        self.assertEqual(self.client.post('/mark_contacted/missing', data={'csrf_token': 'test-csrf'},
                                        headers={'X-CSRF-Token': '', 'Origin': 'http://localhost'}).status_code, 404)

    def test_background_run_guard_and_observed_errors(self):
        import threading
        import time
        started, release = threading.Event(), threading.Event()
        def fake_run():
            started.set()
            release.wait(3)
            return {'craigslist': {'found': 0, 'new': 0, 'err': 'HTTP 403 blocked'}}
        with patch('run.run_all', side_effect=fake_run):
            try:
                # Prevent the old GET implementation spawning an actual scraper.
                with patch('subprocess.Popen'):
                    self.assertEqual(self.client.get('/run').status_code, 405)
                self.assertEqual(self.client.post('/run').status_code, 202)
                self.assertTrue(started.wait(1))
                self.assertTrue(self.client.get('/scrape-status').json['running'])
                self.assertEqual(self.client.post('/run').status_code, 409)
                self.assertEqual(self.client.get('/').status_code, 200)
            finally:
                release.set()
            for _ in range(100):
                status = self.client.get('/scrape-status').json
                if not status['running']:
                    break
                time.sleep(.01)
            self.assertEqual(status['status'], 'completed_with_errors')
            self.assertIn('403', status['results']['craigslist']['err'])

    def test_dashboard_shows_real_logs_manual_resources_and_mobile_styles(self):
        database.init_db()
        conn = database.get_conn()
        conn.execute('INSERT INTO scrape_log (source, found, new_leads, error, created_at) VALUES (?, ?, ?, ?, ?)',
                     ('craigslist', 0, 0, 'HTTP 403 blocked', '2026-01-01T00:00:00'))
        conn.commit()
        conn.close()
        status = self.client.get('/scrape-status').json
        self.assertTrue('recent_logs' in status)
        self.assertEqual(status['recent_logs'][0]['status'], 'blocked')
        html = self.client.get('/').get_data(as_text=True)
        for text in ('HTTP 403 blocked', 'Manual research resources', 'not a valuation', 'id="run-form"',
                     'id="run-status"', '@media(max-width:480px)', 'zillow.com', 'facebook.com/marketplace'):
            self.assertTrue(text in html, text)
        self.assertFalse('aggregates ALL' in html)
        self.assertFalse('daily manual-check reminders' in html)
        self.assertEqual(database.get_stats()['total'], 0)

    def test_run_form_submits_its_own_csrf_and_returns_to_dashboard(self):
        from bs4 import BeautifulSoup
        form = BeautifulSoup(self.client.get('/').data, 'html.parser').select_one('#run-form')
        token = form.select_one('input[name="csrf_token"]')
        self.assertIsNotNone(token, 'Run Scraper form must include its own CSRF token')
        with patch('app.threading.Thread'):
            import app as dashboard
            with patch.dict(dashboard._run_state, running=False):
                response = self.client.post('/run', data={'csrf_token': token['value']},
                    headers={'X-CSRF-Token': '', 'Accept': 'text/html'})
                self.assertEqual(response.status_code, 303)
                self.assertEqual(response.location, '/')

    def test_bad_filter_is_400_not_crash(self):
        self.assertEqual(self.client.get('/?min_score=oops').status_code, 400)


if __name__ == '__main__':
    unittest.main()
