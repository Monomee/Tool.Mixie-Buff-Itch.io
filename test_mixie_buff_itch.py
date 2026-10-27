import csv
import queue
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from playwright.sync_api import sync_playwright

import mixie_buff_itch as gui


class DownloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.requests = []

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                cls.requests.append(self.path)
                if self.path == '/file':
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/octet-stream')
                    self.send_header('Content-Disposition', 'attachment; filename="sample.apk"')
                    self.send_header('Content-Length', str(4 * 1024 * 1024))
                    self.end_headers()
                    try:
                        for _ in range(256):
                            self.wfile.write(b'x' * 16384)
                            self.wfile.flush()
                            time.sleep(0.02)
                    except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                        pass
                    return
                pages = {
                    '/game': '<a href="/purchase">Download Now</a><a href="/play">Run game</a>',
                    '/direct': '<a href="/downloads">Download Now</a>',
                    '/popup-game': '<a href="/popup-purchase">Download Now</a>',
                    '/popup-purchase': '''<a class="direct_download_btn" href="#" onclick="
                        const popup = window.open();
                        popup.document.write('Loading...');
                        setTimeout(() => { popup.location = '/downloads'; }, 200);
                        return false;">No thanks, just take me to the downloads</a>''',
                    '/purchase': '<a class="direct_download_btn" href="/downloads">No thanks, just take me to the downloads</a><form action="/pay"><button>Pay</button></form>',
                    '/downloads': '<div class="upload"><a class="button download_btn" href="/file">Download</a></div>',
                    '/paid': '<a href="/checkout">Download Now</a>',
                    '/checkout': '<form action="/pay"><button>Buy now</button></form>',
                }
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(pages.get(self.path, '').encode())

            def log_message(self, *args):
                pass

        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.server.daemon_threads = True
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}'
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join()

    def setUp(self):
        self.requests.clear()
        self.context = self.browser.new_context(accept_downloads=True)
        self.page = self.context.new_page()

    def tearDown(self):
        self.context.close()

    def test_donation_flow_starts_and_cancels_one_file(self):
        downloads = []
        self.page.on('download', lambda download: downloads.append(download))
        self.page.goto(self.url + '/game')
        status, filename = gui.auto_download(self.page)
        self.assertEqual((status, filename), ('download_cancelled', 'sample.apk'))
        self.assertEqual(len(downloads), 1)
        self.assertEqual(downloads[0].failure(), 'canceled')
        self.assertEqual(self.requests.count('/file'), 1)
        self.assertNotIn('/play', self.requests)
        self.assertNotIn('/pay', self.requests)

    def test_free_download_page_without_donation_step(self):
        self.page.goto(self.url + '/direct')
        self.assertEqual(gui.auto_download(self.page), ('download_cancelled', 'sample.apk'))
        self.assertNotIn('/purchase', self.requests)

    def test_html_game_download_follows_new_tab_after_skipping_donation(self):
        self.page.goto(self.url + '/popup-game')
        self.assertEqual(gui.auto_download(self.page), ('download_cancelled', 'sample.apk'))
        self.assertTrue(self.page.url.endswith('/popup-purchase'))
        self.assertEqual(len(self.context.pages), 2)
        self.assertTrue(self.context.pages[1].url.endswith('/downloads'))
        self.assertEqual(self.requests.count('/file'), 1)

    def test_paid_only_page_fails_without_buying(self):
        row = self.run_session(download=True, path='/paid')
        self.assertEqual(row['status'], 'error')
        self.assertEqual(row['download_action'], 'failed')
        self.assertIn('TimeoutError', row['page_errors'])
        self.assertNotIn('/pay', self.requests)
        self.assertNotIn('/file', self.requests)


    def run_session(self, download, path='/game'):
        with tempfile.TemporaryDirectory(dir=gui.APP_DIR) as folder:
            app = gui.App.__new__(gui.App)
            app.profile_dir = Path(folder) / 'profiles'
            profile = app.profile_dir / 'user_001'
            profile.mkdir(parents=True)
            marker = profile / 'keep.txt'
            marker.write_text('existing profile', encoding='utf-8')
            app.report_dir = Path(folder)
            app.events = queue.Queue()
            app.stop_event = threading.Event()
            opts = dict(url=self.url + path, browser='Chromium', headless=True,
                        auto=False, mute=True, download=download, duration=0, pause=0)
            worker = threading.Thread(target=app.execute, args=(['user_001'], opts), daemon=True)
            worker.start()
            worker.join(timeout=30)
            self.assertFalse(worker.is_alive(), 'Session failed to finish')
            self.assertEqual(marker.read_text(encoding='utf-8'), 'existing profile')
            self.assertEqual([p.name for p in app.profile_dir.iterdir()], ['user_001'])
            with next(Path(folder).glob('*.csv')).open(encoding='utf-8-sig', newline='') as report:
                rows = list(csv.DictReader(report))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['profile_reused'], 'True')
            return rows[0]

    def test_download_session_reuses_profile_and_records_cancelled_file(self):
        row = self.run_session(download=True, path='/popup-game')
        self.assertEqual(row['status'], 'download_cancelled')
        self.assertEqual(row['download_action'], 'sample.apk')
        self.assertEqual(row['play_action'], 'disabled')
        self.assertEqual(row['page_errors'], '')
        self.assertEqual(self.requests.count('/file'), 1)

    def test_game_session_does_not_download_when_option_is_off(self):
        row = self.run_session(download=False)
        self.assertEqual(row['status'], 'page_opened_no_iframe')
        self.assertEqual(row['download_action'], 'disabled')
        self.assertNotIn('/file', self.requests)


class SettingsTests(unittest.TestCase):
    def test_download_option_is_saved_and_passed_to_session(self):
        with tempfile.TemporaryDirectory(dir=gui.APP_DIR) as folder:
            settings = Path(folder) / 'settings.json'
            with patch.object(gui, 'SETTINGS_FILE', settings):
                app = gui.App.__new__(gui.App)
                values = dict(url=gui.DEFAULT_URL, browser='Chromium', count='1', duration='10',
                              pause='0', auto=True, mute=True, headless=True, download=True)
                app.language_code = 'en'
                for key, value in values.items():
                    setattr(app, key, SimpleNamespace(get=lambda value=value: value))
                self.assertTrue(app.validate()['download'])
                self.assertTrue(app.read_settings()['download'])
                self.assertEqual(app.read_settings()['language'], 'en')


class LanguageTests(unittest.TestCase):
    def test_switch_saves_language_and_translates_current_status(self):
        with tempfile.TemporaryDirectory(dir=gui.APP_DIR) as folder:
            with patch.object(gui, 'SETTINGS_FILE', Path(folder) / 'settings.json'):
                app = gui.App.__new__(gui.App)
                values = dict(url=gui.DEFAULT_URL, browser='Chromium', count='2', duration='30',
                              pause='5', auto=True, mute=True, headless=False, download=False,
                              language='English')
                for key, value in values.items():
                    setattr(app, key, SimpleNamespace(get=lambda value=value: value))
                label, status = {}, []
                app.translated_widgets = [(SimpleNamespace(configure=lambda **kw: label.update(kw)), 'Tạo & chạy profile mới')]
                app.status = SimpleNamespace(set=status.append)
                app.status_message = ('Đang chạy {current}/{total}', dict(current=1, total=2))
                app.change_language()
                self.assertEqual(label['text'], 'Create & run new profiles')
                self.assertEqual(status[-1], 'Running 1/2')
                self.assertEqual(app.read_settings()['language'], 'en')
                self.assertEqual(app.read_settings()['duration'], '30')
                app.language = SimpleNamespace(get=lambda: 'Tiếng Việt')
                app.change_language()
                self.assertEqual(label['text'], 'Tạo & chạy profile mới')
                self.assertEqual(status[-1], 'Đang chạy 1/2')
                self.assertEqual(app.read_settings()['language'], 'vi')

    def test_translation_formats_messages_and_defaults_to_vietnamese(self):
        app = gui.App.__new__(gui.App)
        self.assertEqual(app.tr('Đang chạy {current}/{total}', current=1, total=3), 'Đang chạy 1/3')
        app.language_code = 'en'
        self.assertEqual(app.tr('Đang chạy {current}/{total}', current=1, total=3), 'Running 1/3')
        self.assertEqual(app.tr('Tạo & chạy profile mới'), 'Create & run new profiles')

    def test_switch_updates_ui_preserves_state_and_restores_saved_language(self):
        with tempfile.TemporaryDirectory(dir=gui.APP_DIR) as folder:
            with patch.object(gui, 'APP_DIR', Path(folder)), patch.object(gui, 'SETTINGS_FILE', Path(folder) / 'settings.json'):
                for saved_language in (False, True):
                    try:
                        root = gui.tk.Tk()
                    except gui.tk.TclError as error:
                        self.skipTest(f'Tk unavailable: {error}')
                    root.withdraw()
                    try:
                        app = gui.App(root)
                        if not saved_language:
                            self.assertEqual(app.new_button.cget('text'), 'Tạo & chạy profile mới')
                            app.url.set('https://example.itch.io/test')
                            app.log.configure(state='normal')
                            app.log.insert('end', 'existing log')
                            app.language.set('English')
                            app.change_language()
                        self.assertEqual(app.new_button.cget('text'), 'Create & run new profiles')
                        self.assertEqual(app.url.get(), 'https://example.itch.io/test')
                        self.assertEqual(app.read_settings()['language'], 'en')
                        self.assertEqual(app.tr('Đang chạy {current}/{total}', current=1, total=3), 'Running 1/3')
                        if not saved_language:
                            self.assertEqual(app.log.get('1.0', 'end-1c'), 'existing log')
                            app.language.set('Tiếng Việt')
                            app.change_language()
                            self.assertEqual(app.new_button.cget('text'), 'Tạo & chạy profile mới')
                            app.language.set('English')
                            app.change_language()
                    finally:
                        root.destroy()


if __name__ == '__main__':
    unittest.main()
