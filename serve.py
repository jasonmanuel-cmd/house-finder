"""Single-process production server for Windows, Linux, and Render."""
import os
from waitress import serve as waitress_serve
from app import app
from database import init_db


def main():
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', '5000'))
    if host not in ('127.0.0.1', 'localhost', '::1') and not os.environ.get('DASHBOARD_TOKEN'):
        raise SystemExit('Public binding requires DASHBOARD_TOKEN. Use localhost for private local access.')
    init_db()
    print(f'Private Seller Dashboard: http://{host}:{port}', flush=True)
    waitress_serve(app, host=host, port=port, threads=8)


if __name__ == '__main__':
    main()
