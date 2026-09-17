import importlib
import os
import unittest
from unittest.mock import patch

class ServeTests(unittest.TestCase):
    def test_default_is_localhost_and_initializes_database(self):
        import serve
        with patch.dict(os.environ, {}, clear=True), patch('serve.init_db') as init, patch('serve.waitress_serve') as run:
            serve.main()
            init.assert_called_once()
            self.assertEqual(run.call_args.kwargs['host'], '127.0.0.1')
            self.assertEqual(run.call_args.kwargs['port'], 5000)

    def test_public_bind_requires_auth(self):
        import serve
        with patch.dict(os.environ, {'HOST': '0.0.0.0'}, clear=True):
            with self.assertRaises(SystemExit):
                serve.main()

if __name__ == '__main__':
    unittest.main()
