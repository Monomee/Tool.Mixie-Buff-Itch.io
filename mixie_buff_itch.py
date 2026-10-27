"""mixie-buff-itch: itch.io WebGL QA GUI (local, small-scale)."""
import csv
import json
import queue
import re
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
import tkinter as tk
from tkinter import ttk, messagebox

APP_DIR = Path(__file__).resolve().parent
SETTINGS_FILE = APP_DIR / 'mixie-buff-itch_settings.json'
DEFAULT_URL = 'https://monomee.itch.io/mixie-empire-boba-and-ice-cream'
MAX_NEW_PROFILES = 100
CSV_FIELDS = ['timestamp_utc','profile','profile_reused','browser','status','play_action','ga_requests','ga_hosts','iframe_count','page_errors','download_action']
ENGLISH = {
    'WEBGL QA TESTER  /  Kiểm thử game với profile trình duyệt độc lập': 'WEBGL QA TESTER  /  Test games with independent browser profiles',
    'Ngôn ngữ': 'Language',
    'Game & trình duyệt': 'Game & browser',
    'Trình duyệt': 'Browser',
    'Tự nhấn Run game': 'Auto-click Run game',
    'Tắt âm thanh': 'Mute audio',
    'Chạy ẩn (headless; có thể lỗi WebGL)': 'Headless (may cause WebGL issues)',
    'Download rồi hủy file (thay cho chạy game)': 'Download then cancel (instead of running game)',
    'Tạo phiên kiểm thử mới': 'Create new test sessions',
    f'Số profile mới (1–{MAX_NEW_PROFILES})': f'New profiles (1–{MAX_NEW_PROFILES})',
    'Thời lượng mỗi phiên (giây)': 'Session duration (seconds)',
    'Nghỉ giữa các phiên (giây)': 'Pause between sessions (seconds)',
    'Các profile chạy lần lượt, mỗi lần một phiên.': 'Profiles run sequentially, one session at a time.',
    'Tạo & chạy profile mới': 'Create & run new profiles',
    'Chạy lại profile đã lưu': 'Reuse saved profiles',
    'Giữ Ctrl / Shift để chọn nhiều profile.': 'Hold Ctrl / Shift to select multiple profiles.',
    'Làm mới': 'Refresh',
    'Chọn tất cả': 'Select all',
    'Thư mục': 'Folder',
    'Chạy profile đã chọn': 'Run selected profiles',
    'Sẵn sàng': 'Ready',
    'Dừng sau phiên hiện tại': 'Stop after current session',
    'Mở báo cáo': 'Open reports',
    'Nhật ký kiểm thử': 'Test log',
    'Nên dùng GameAnalytics TEST để tránh ảnh hưởng số liệu thật.': 'Use a GameAnalytics TEST project to avoid affecting production metrics.',
    'URL phải là trang itch.io sử dụng HTTPS.': 'URL must be an itch.io page using HTTPS.',
    'Giới hạn: 1–{maximum} profile mới, mỗi phiên 10–3600 giây, nghỉ 0–600 giây.': 'Limits: 1–{maximum} new profiles, 10–3600 seconds per session, 0–600 seconds between sessions.',
    'Cấu hình không hợp lệ': 'Invalid settings',
    'Chưa chọn': 'Nothing selected',
    'Hãy chọn một hoặc nhiều profile trong danh sách.': 'Select one or more profiles from the list.',
    'Đang chạy {current}/{total}': 'Running {current}/{total}',
    'Đang chạy {current}/{total} — {name}': 'Running {current}/{total} — {name}',
    'Download rồi hủy file': 'Download then cancel',
    '{duration}s/phiên': '{duration}s/session',
    'Bắt đầu: {count} profile | {browser} | {mode}': 'Starting: {count} profiles | {browser} | {mode}',
    'Đã yêu cầu dừng; sẽ hoàn tất phiên đang chạy.': 'Stop requested; the current session will finish first.',
    'Chưa cài Playwright. Chạy: pip install playwright; python -m playwright install chromium': 'Playwright is not installed. Run: pip install playwright; python -m playwright install chromium',
    'Không tìm thấy Brave tại đường dẫn cài mặc định. Chọn Chromium hoặc cài Brave.': 'Brave was not found in the default locations. Select Chromium or install Brave.',
    'Đã xuất báo cáo: {report}': 'Report saved: {report}',
    'Lỗi khởi chạy: {error}': 'Launch error: {error}',
    'Đã hoàn tất': 'Completed',
    'Đã dừng': 'Stopped',
    'Đang chạy': 'Running',
    'Hãy nhấn Dừng và đợi phiên hiện tại hoàn tất trước khi đóng.': 'Click Stop and wait for the current session to finish before closing.',
    'Không lưu được ngôn ngữ': 'Could not save language',
}


def auto_play(page):
    selectors = [
        '.load_iframe_btn', '.iframe_placeholder .load_iframe_btn',
        '.game_frame .button', 'button:has-text("Run game")',
        'a:has-text("Run game")', 'button:has-text("Play game")',
        'a:has-text("Play game")',
    ]
    for selector in selectors:
        try:
            target = page.locator(selector).first
            if target.count() and target.is_visible():
                target.click(timeout=5000)
                return 'clicked: ' + selector
        except Exception:
            pass
    return 'iframe present' if len(page.frames) > 1 else 'play button not found'


def auto_download(page):
    download_button = '.upload .download_btn:visible'
    page.get_by_role('link', name=re.compile(r'^Download Now$', re.I)).first.click(timeout=15000)
    page.locator(f'.direct_download_btn:visible, {download_button}').first.wait_for(timeout=15000)
    skip = page.locator('.direct_download_btn:visible')
    if skip.count():
        existing_pages = set(page.context.pages)
        skip.first.click(timeout=15000)
        # HTML games can open the download page in a new tab after skipping payment.
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            candidates = [page] + [tab for tab in page.context.pages if tab not in existing_pages]
            target = next((tab for tab in candidates if not tab.is_closed() and tab.locator(download_button).count()), None)
            if target is not None:
                page = target
                break
            page.wait_for_timeout(100)
        else:
            raise RuntimeError('Download button not found in the current or new download tab after 15 seconds.')
    with page.expect_download(timeout=30000) as pending:
        page.locator(download_button).first.click(timeout=15000)
    download = pending.value
    download.cancel()
    failure = download.failure()
    if failure and failure != 'canceled':
        raise RuntimeError(f'Download failed: {failure}')
    status = 'download_cancelled' if failure else 'download_completed_before_cancel'
    return status, download.suggested_filename


def locate_brave():
    paths = [Path(r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe'),
             Path(r'C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe'),
             Path.home() / r'AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe']
    return next((str(p) for p in paths if p.is_file()), None)


class App:
    def __init__(self, root):
        self.root = root
        root.title('mixie-buff-itch | WebGL QA Tester')
        root.geometry('1080x820')
        root.minsize(940, 760)
        self.events = queue.Queue()
        self.stop_event = threading.Event()
        self.running = False
        self.worker = None
        saved = self.read_settings()
        self.language_code = 'en' if saved.get('language') == 'en' else 'vi'
        self.language = tk.StringVar(value='English' if self.language_code == 'en' else 'Tiếng Việt')
        self.url = tk.StringVar(value=saved.get('url', DEFAULT_URL))
        self.browser = tk.StringVar(value=saved.get('browser', 'Chromium'))
        self.count = tk.StringVar(value=str(saved.get('count', 3)))
        self.duration = tk.StringVar(value=str(saved.get('duration', 90)))
        self.pause = tk.StringVar(value=str(saved.get('pause', 5)))
        self.auto = tk.BooleanVar(value=saved.get('auto', True))
        self.download = tk.BooleanVar(value=saved.get('download', False))
        self.mute = tk.BooleanVar(value=saved.get('mute', True))
        self.headless = tk.BooleanVar(value=saved.get('headless', False))
        self.profile_dir = APP_DIR / 'mixie-buff-itch_profiles'
        self.report_dir = APP_DIR / 'mixie-buff-itch_reports'
        self.profile_dir.mkdir(exist_ok=True)
        self.report_dir.mkdir(exist_ok=True)
        self.build_ui()
        self.refresh_profiles()
        self.root.after(100, self.drain_events)
        self.root.protocol('WM_DELETE_WINDOW', self.close)

    def read_settings(self):
        try:
            return json.loads(SETTINGS_FILE.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            return {}

    def save_settings(self):
        data = dict(url=self.url.get(), browser=self.browser.get(), count=self.count.get(),
                    duration=self.duration.get(), pause=self.pause.get(), auto=self.auto.get(),
                    mute=self.mute.get(), headless=self.headless.get(), download=self.download.get(),
                    language=getattr(self, 'language_code', 'vi'))
        SETTINGS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')

    def tr(self, text, **values):
        if getattr(self, 'language_code', 'vi') == 'en':
            text = ENGLISH.get(text, text)
        return text.format(**values)

    def set_status(self, text, **values):
        self.status_message = (text, values)
        self.status.set(self.tr(text, **values))

    def apply_language(self):
        for widget, text in self.translated_widgets:
            widget.configure(text=self.tr(text))
        text, values = self.status_message
        self.set_status(text, **values)

    def change_language(self, event=None):
        self.language_code = 'en' if self.language.get() == 'English' else 'vi'
        self.apply_language()
        try:
            self.save_settings()
        except OSError as error:
            messagebox.showerror(self.tr('Không lưu được ngôn ngữ'), str(error))

    def build_ui(self):
        self.root.configure(background='#f3f6fb')
        self.root.option_add('*Font', ('Segoe UI', 10))
        style = ttk.Style(self.root)
        style.configure('.', font=('Segoe UI', 10))
        style.configure('TFrame', background='#f3f6fb')
        style.configure('TLabel', background='#f3f6fb', foreground='#172b4d')
        style.configure('TLabelframe', background='#f3f6fb', borderwidth=1)
        style.configure('TLabelframe.Label', background='#f3f6fb', foreground='#172b4d', font=('Segoe UI', 11, 'bold'))
        style.configure('TCheckbutton', background='#f3f6fb')
        style.configure('TButton', padding=(12, 8))
        style.configure('TEntry', padding=6)
        style.configure('TSpinbox', padding=6)
        style.configure('TCombobox', padding=6)
        style.configure('Accent.TButton', background='#2563eb', foreground='white', font=('Segoe UI', 10, 'bold'))
        style.map('Accent.TButton', background=[('disabled', '#cbd5e1'), ('active', '#1d4ed8')], foreground=[('disabled', '#64748b')])
        pane = ttk.Frame(self.root, padding=20)
        pane.pack(fill='both', expand=True)
        header = ttk.Frame(pane)
        header.pack(fill='x')
        ttk.Label(header, text='mixie-buff-itch', font=('Segoe UI', 23, 'bold')).pack(side='left')
        self.language_picker = ttk.Combobox(header, textvariable=self.language, state='readonly', values=['Tiếng Việt', 'English'], width=12)
        self.language_picker.pack(side='right')
        self.language_picker.bind('<<ComboboxSelected>>', self.change_language)
        ttk.Label(header, text='Ngôn ngữ').pack(side='right', padx=8)
        ttk.Label(pane, text='WEBGL QA TESTER  /  Kiểm thử game với profile trình duyệt độc lập', foreground='#64748b').pack(anchor='w', pady=(2, 16))

        general = ttk.LabelFrame(pane, text='Game & trình duyệt', padding=14)
        general.pack(fill='x')
        general.columnconfigure(1, weight=1)
        ttk.Label(general, text='URL itch.io').grid(row=0, column=0, sticky='w', padx=(0, 12))
        ttk.Entry(general, textvariable=self.url).grid(row=0, column=1, columnspan=3, sticky='ew')
        ttk.Label(general, text='Trình duyệt').grid(row=1, column=0, sticky='w', pady=(12, 0))
        ttk.Combobox(general, textvariable=self.browser, state='readonly', values=['Chromium', 'Brave'], width=14).grid(row=1, column=1, sticky='w', pady=(12, 0))
        ttk.Checkbutton(general, text='Tự nhấn Run game', variable=self.auto).grid(row=1, column=2, sticky='w', padx=12, pady=(12, 0))
        ttk.Checkbutton(general, text='Tắt âm thanh', variable=self.mute).grid(row=1, column=3, sticky='w', pady=(12, 0))
        ttk.Checkbutton(general, text='Chạy ẩn (headless; có thể lỗi WebGL)', variable=self.headless).grid(row=2, column=1, columnspan=3, sticky='w', pady=(8, 0))
        ttk.Checkbutton(general, text='Download rồi hủy file (thay cho chạy game)', variable=self.download).grid(row=3, column=1, columnspan=3, sticky='w', pady=(8, 0))

        columns = ttk.Frame(pane)
        columns.pack(fill='both', expand=True, pady=14)
        columns.columnconfigure(0, weight=1, uniform='column')
        columns.columnconfigure(1, weight=1, uniform='column')
        columns.rowconfigure(0, weight=1)
        options = ttk.LabelFrame(columns, text='Tạo phiên kiểm thử mới', padding=14)
        options.grid(row=0, column=0, sticky='nsew', padx=(0, 7))
        options.columnconfigure(0, weight=1)
        for row, (label, variable, low, high) in enumerate([
            (f'Số profile mới (1–{MAX_NEW_PROFILES})', self.count, 1, MAX_NEW_PROFILES),
            ('Thời lượng mỗi phiên (giây)', self.duration, 10, 3600),
            ('Nghỉ giữa các phiên (giây)', self.pause, 0, 600),
        ]):
            ttk.Label(options, text=label).grid(row=row, column=0, sticky='w', pady=(0, 12))
            ttk.Spinbox(options, textvariable=variable, from_=low, to=high, width=8).grid(row=row, column=1, sticky='e', padx=(12, 0), pady=(0, 12))
        ttk.Label(options, text='Các profile chạy lần lượt, mỗi lần một phiên.', foreground='#64748b').grid(row=3, column=0, columnspan=2, sticky='w', pady=(0, 12))
        self.new_button = ttk.Button(options, text='Tạo & chạy profile mới', style='Accent.TButton', command=self.start_new)
        self.new_button.grid(row=4, column=0, columnspan=2, sticky='ew')

        profiles = ttk.LabelFrame(columns, text='Chạy lại profile đã lưu', padding=14)
        profiles.grid(row=0, column=1, sticky='nsew', padx=(7, 0))
        ttk.Label(profiles, text='Giữ Ctrl / Shift để chọn nhiều profile.', foreground='#64748b').pack(anchor='w', pady=(0, 8))
        row = ttk.Frame(profiles)
        row.pack(fill='both', expand=True)
        self.profile_list = tk.Listbox(row, selectmode='extended', height=5, exportselection=False, background='white', foreground='#172b4d', selectbackground='#2563eb', selectforeground='white', relief='flat', highlightthickness=1, highlightbackground='#cbd5e1', font=('Consolas', 11))
        self.profile_list.pack(side='left', fill='both', expand=True)
        scroll = ttk.Scrollbar(row, orient='vertical', command=self.profile_list.yview)
        scroll.pack(side='right', fill='y')
        self.profile_list.configure(yscrollcommand=scroll.set)
        actions = ttk.Frame(profiles)
        actions.pack(fill='x', pady=8)
        ttk.Button(actions, text='Làm mới', command=self.refresh_profiles).pack(side='left')
        ttk.Button(actions, text='Chọn tất cả', command=lambda: self.profile_list.select_set(0, tk.END)).pack(side='left', padx=6)
        ttk.Button(actions, text='Thư mục', command=lambda: self.open_folder(self.profile_dir)).pack(side='right')
        self.existing_button = ttk.Button(profiles, text='Chạy profile đã chọn', command=self.start_existing)
        self.existing_button.pack(fill='x')

        toolbar = ttk.Frame(pane)
        toolbar.pack(fill='x', pady=(0, 8))
        self.status = tk.StringVar(value='Sẵn sàng')
        self.status_message = ('Sẵn sàng', {})
        ttk.Label(toolbar, textvariable=self.status, font=('Segoe UI', 11, 'bold')).pack(side='left')
        self.stop_button = ttk.Button(toolbar, text='Dừng sau phiên hiện tại', command=self.stop, state='disabled')
        self.stop_button.pack(side='right', padx=(8, 0))
        ttk.Button(toolbar, text='Mở báo cáo', command=lambda: self.open_folder(self.report_dir)).pack(side='right')
        self.progress = ttk.Progressbar(pane, mode='determinate')
        self.progress.pack(fill='x', pady=(0, 12))
        ttk.Label(pane, text='Nhật ký kiểm thử', font=('Segoe UI', 11, 'bold')).pack(anchor='w')
        logframe = ttk.Frame(pane)
        logframe.pack(fill='both', expand=True, pady=(6, 8))
        self.log = tk.Text(logframe, height=7, wrap='word', state='disabled', font=('Consolas', 10), background='#102039', foreground='#e2e8f0', relief='flat', padx=12, pady=10)
        self.log.pack(side='left', fill='both', expand=True)
        scroll = ttk.Scrollbar(logframe, orient='vertical', command=self.log.yview)
        scroll.pack(side='right', fill='y')
        self.log.configure(yscrollcommand=scroll.set)
        ttk.Label(pane, text='Nên dùng GameAnalytics TEST để tránh ảnh hưởng số liệu thật.', foreground='#64748b').pack(anchor='w')
        self.translated_widgets = []
        pending = [pane]
        while pending:
            widget = pending.pop()
            pending.extend(widget.winfo_children())
            if 'text' in widget.keys() and widget.cget('text') in ENGLISH:
                self.translated_widgets.append((widget, widget.cget('text')))
        self.apply_language()

    def open_folder(self,path):
        import os, subprocess, sys
        if sys.platform == 'win32': os.startfile(str(path))
        elif sys.platform == 'darwin': subprocess.Popen(['open',str(path)])
        else: subprocess.Popen(['xdg-open',str(path)])

    def refresh_profiles(self):
        self.profile_list.delete(0,tk.END)
        self.profiles = sorted(p.name for p in self.profile_dir.glob('user_*') if p.is_dir())
        for name in self.profiles: self.profile_list.insert(tk.END,name)

    def validate(self):
        u=self.url.get().strip()
        host=(urlparse(u).hostname or '').lower()
        if not (u.startswith('https://') and (host == 'itch.io' or host.endswith('.itch.io'))):
            raise ValueError(self.tr('URL phải là trang itch.io sử dụng HTTPS.'))
        d=int(self.duration.get()); p=int(self.pause.get()); n=int(self.count.get())
        if not (10 <= d <= 3600 and 0 <= p <= 600 and 1 <= n <= MAX_NEW_PROFILES):
            raise ValueError(self.tr('Giới hạn: 1–{maximum} profile mới, mỗi phiên 10–3600 giây, nghỉ 0–600 giây.', maximum=MAX_NEW_PROFILES))
        self.save_settings()
        return dict(url=u,duration=d,pause=p,browser=self.browser.get(),auto=self.auto.get(),mute=self.mute.get(),headless=self.headless.get(),download=self.download.get())

    def start_new(self):
        try:
            opts=self.validate()
            n=int(self.count.get())
            indices=[int(m.group(1)) for p in self.profiles if (m:=re.fullmatch(r'user_(\d+)',p))]
            start=max(indices,default=0)+1
            names=[f'user_{i:03d}' for i in range(start,start+n)]
            self.begin(names,opts)
        except (ValueError,OSError) as e: messagebox.showerror(self.tr('Cấu hình không hợp lệ'),str(e))

    def start_existing(self):
        try:
            opts=self.validate()
            names=[self.profiles[i] for i in self.profile_list.curselection()]
            if not names:
                messagebox.showinfo(self.tr('Chưa chọn'),self.tr('Hãy chọn một hoặc nhiều profile trong danh sách.'))
                return
            self.begin(names,opts)
        except (ValueError,OSError) as e: messagebox.showerror(self.tr('Cấu hình không hợp lệ'),str(e))

    def begin(self,names,opts):
        if self.running: return
        self.running=True
        self.stop_event.clear()
        self.stop_button.configure(state='normal')
        self.new_button.configure(state='disabled')
        self.existing_button.configure(state='disabled')
        self.progress.configure(maximum=len(names), value=0)
        self.set_status('Đang chạy {current}/{total}', current=0, total=len(names))
        mode=self.tr('Download rồi hủy file') if opts.get('download') else self.tr('{duration}s/phiên', duration=opts['duration'])
        self.write_log(self.tr('Bắt đầu: {count} profile | {browser} | {mode}', count=len(names), browser=opts['browser'], mode=mode))
        self.worker=threading.Thread(target=self.execute,args=(names,opts),daemon=True)
        self.worker.start()

    def stop(self):
        self.stop_event.set()
        self.write_log(self.tr('Đã yêu cầu dừng; sẽ hoàn tất phiên đang chạy.'))

    def execute(self,names,opts):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.events.put(('log',self.tr('Chưa cài Playwright. Chạy: pip install playwright; python -m playwright install chromium')))
            self.events.put(('finished',None)); return
        brave=locate_brave() if opts['browser']=='Brave' else None
        if opts['browser']=='Brave' and not brave:
            self.events.put(('log',self.tr('Không tìm thấy Brave tại đường dẫn cài mặc định. Chọn Chromium hoặc cài Brave.')))
            self.events.put(('finished',None)); return
        report=self.report_dir / ('mixie-buff-itch_' + datetime.now().strftime('%Y%m%d_%H%M%S')+'.csv')
        try:
            with sync_playwright() as pw, report.open('w',encoding='utf-8-sig',newline='') as fh:
                writer=csv.DictWriter(fh,fieldnames=CSV_FIELDS); writer.writeheader()
                for i,name in enumerate(names,1):
                    if self.stop_event.is_set(): break
                    self.events.put(('status',('Đang chạy {current}/{total} — {name}', dict(current=i, total=len(names), name=name))))
                    profile=self.profile_dir/name
                    existed=profile.is_dir() and any(profile.iterdir())
                    row={'timestamp_utc':datetime.now(timezone.utc).isoformat(),'profile':name,'profile_reused':existed,
                         'browser':opts['browser'],'status':'unknown','play_action':'disabled','ga_requests':0,
                         'ga_hosts':'','iframe_count':0,'page_errors':'','download_action':'not_started' if opts.get('download') else 'disabled'}
                    ga=[]; errors=[]; context=None
                    try:
                        args=['--enable-webgl','--use-gl=angle']
                        if opts['mute']: args.append('--mute-audio')
                        kw={'headless':opts['headless'],'viewport':{'width':1280,'height':800},'args':args,'accept_downloads':True}
                        if brave: kw['executable_path']=brave
                        context=pw.chromium.launch_persistent_context(str(profile),**kw)
                        context.on('request',lambda req:ga.append(req.url) if 'gameanalytics' in req.url.lower() else None)
                        context.on('page',lambda pg:pg.on('pageerror',lambda err:errors.append(str(err)[:300])))
                        page=context.pages[0] if context.pages else context.new_page()
                        page.on('pageerror',lambda err:errors.append(str(err)[:300]))
                        page.goto(opts['url'],wait_until='domcontentloaded',timeout=60000)
                        page.wait_for_timeout(1800)
                        if opts.get('download'):
                            row['status'],row['download_action']=auto_download(page)
                            self.events.put(('log',f'{name}: {row["status"]}; file={row["download_action"]}'))
                        else:
                            row['play_action']=auto_play(page) if opts['auto'] else 'disabled'
                            self.events.put(('log',f'{name}: {row["play_action"]}'))
                            end=time.monotonic()+opts['duration']
                            while time.monotonic()<end:
                                page.wait_for_timeout(min(1000,max(1,int((end-time.monotonic())*1000))))
                            row['iframe_count']=len(page.frames)-1
                            row['status']='game_iframe_detected' if row['iframe_count'] else 'page_opened_no_iframe'
                    except Exception as e:
                        row['status']='error'
                        if opts.get('download'): row['download_action']='failed'
                        errors.append(f'{type(e).__name__}: {e}'[:400])
                    finally:
                        if context is not None:
                            try:context.close()
                            except Exception:pass
                    row['ga_requests']=len(ga)
                    row['ga_hosts']=';'.join(sorted(set(urlparse(u).hostname or '' for u in ga)))
                    row['page_errors']=' | '.join(errors[:3])
                    writer.writerow(row);fh.flush()
                    self.events.put(('progress', i))
                    self.events.put(('log',f'{name}: {row["status"]}; GA requests={len(ga)}; errors={len(errors)}'))
                    if i<len(names) and not self.stop_event.is_set():
                        self.stop_event.wait(opts['pause'])
                self.events.put(('log',self.tr('Đã xuất báo cáo: {report}', report=report)))
        except Exception as e:
            self.events.put(('log',self.tr('Lỗi khởi chạy: {error}', error=f'{type(e).__name__}: {e}')))
        self.events.put(('finished',None))

    def write_log(self,message):
        self.log.configure(state='normal')
        self.log.insert(tk.END,f'[{datetime.now().strftime("%H:%M:%S")}] {message}\n')
        self.log.see(tk.END)
        self.log.configure(state='disabled')

    def drain_events(self):
        try:
            while True:
                kind,data=self.events.get_nowait()
                if kind=='log':self.write_log(data)
                elif kind=='status':self.set_status(data[0], **data[1])
                elif kind=='progress':self.progress.configure(value=data)
                elif kind=='finished':
                    self.running=False
                    self.set_status('Đã hoàn tất' if not self.stop_event.is_set() else 'Đã dừng')
                    self.stop_button.configure(state='disabled')
                    self.new_button.configure(state='normal')
                    self.existing_button.configure(state='normal')
                    self.refresh_profiles()
        except queue.Empty:pass
        self.root.after(100,self.drain_events)

    def close(self):
        if self.running:
            messagebox.showwarning(self.tr('Đang chạy'),self.tr('Hãy nhấn Dừng và đợi phiên hiện tại hoàn tất trước khi đóng.'))
            return
        self.save_settings()
        self.root.destroy()

if __name__=='__main__':
    root=tk.Tk()
    try:
        ttk.Style(root).theme_use('clam')
    except tk.TclError:pass
    App(root)
    root.mainloop()
