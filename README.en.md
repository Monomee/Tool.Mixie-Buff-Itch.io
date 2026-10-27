# mixie-buff-itch

[Tiếng Việt](README.md) | **English**

## Description

`mixie-buff-itch` is a Python GUI tool that uses Playwright to access an itch.io game with independent browser profiles. It creates page visits, attempts to launch/play a WebGL game, or starts and cancels a file download, for learning and experiments with activity commonly described as **“buffing views / downloads / plays”**.

If the game already integrates GameAnalytics, actually launching it may cause the SDK to send events and generate data in that analytics project. The tool observes requests whose URLs contain `gameanalytics`; it does not integrate the SDK, directly submit fabricated events or require a GameAnalytics API key.

**There is no guarantee that each profile counts as a view, download, play or new user.** Separate profiles isolate cookies and storage; they do not change your IP address or guarantee recognition as different users. Check the relevant dashboard for actual results. Use a game and GameAnalytics TEST project you control to avoid distorting production data.

## Features and limits

- Create **1–100 new profiles** per run and retain them for reuse.
- Choose Playwright Chromium or an installed Brave browser.
- Open a game page, attempt to click **Run game / Play game**, then keep the session open for the configured duration. Auto Play does not control characters, complete levels or click every in-game button.
- Download mode clicks **Download Now**, skips the optional donation step if present, clicks the first visible file download button, then cancels. It does not submit payments or bypass mandatory purchases.
- Profiles run **sequentially**, not concurrently. Each run uses game mode or download mode; download mode does not launch the game to generate gameplay events.
- Vietnamese / English interface, local settings and CSV reports.

## Requirements

- Windows 10/11 is the environment covered by these instructions and the BAT launchers.
- Python **3.10 or later**, with Tkinter and pip. The `py` launcher must work to use BAT files.
- Internet access to install dependencies, download the browser and access the game.
- Install Brave separately if you select it. Playwright downloads its own Chromium, separate from your personal Chrome/Brave installation.

## Installation and launch

Clone the repository or download and extract its ZIP. Open a terminal in the folder containing `mixie_buff_itch.py` for the commands below.

### Option 1: BAT files

1. Install Python as described above.
2. Run **`INSTALL_MIXIE_BUFF_ITCH.bat`** once to install dependencies and Chromium. Wait for `Setup complete.`.
3. Run **`RUN_MIXIE_BUFF_ITCH.bat`** to open the tool.

INSTALL runs the first two commands below; RUN changes to the project directory and executes the last command:

```powershell
py -m pip install playwright
py -m playwright install chromium
py mixie_buff_itch.py
```

### Option 2: Review the source and run Python directly

If you are unsure about the BAT files, open them in a text editor, review `mixie_buff_itch.py`, and run the commands yourself:

```powershell
python --version
python -m pip install playwright
python -m playwright install chromium
python mixie_buff_itch.py
```

Both options run **the same source code**. Running directly makes the commands easier to inspect; it does not by itself prove that the code or dependencies are safe. If multiple Python versions are installed, use the same interpreter for installation and launch. You can replace `python` with `py` if that launcher works.

## Configuration

| Field / option | What to enter or select |
| --- | --- |
| Ngôn ngữ / Language | Select **Tiếng Việt** or **English** at the top right. Changes apply immediately and are saved; existing logs and CSV codes stay unchanged. |
| itch.io URL | An HTTPS game page, such as `https://your-studio.itch.io/your-game`. Replace the included example with a game you are authorized to test. Do not enter a direct file download or analytics dashboard URL. |
| Browser | **Chromium** uses the Playwright installation; **Brave** is detected in common Windows installation locations. |
| New profiles | An integer from **1–100**. Controls how many profiles the new-profile button creates; reuse runs the selected profiles in the list. |
| Session duration | An integer from **10–3600 seconds** keeping the session open after navigation and the Auto Play attempt. Ignored in download mode. |
| Pause between sessions | An integer from **0–600 seconds** between profiles. |
| Auto-click Run game | Attempt to find and click a game launch button. Disable it to only open the page; games that start automatically may still launch. Ignored in download mode. |
| Mute audio | Mute browser audio output without changing the game's internal audio settings. |
| Headless | Run without a visible browser window. May cause WebGL issues; leave it off during initial checks so you can observe the browser. |
| Download then cancel | Enable the download-and-cancel flow instead of game mode. Disable it to return to opening/running the game. |

The tool validates all numeric limits above even when reusing profiles or using download mode. Keep these fields valid even when they do not control the selected mode.

### Create new profiles

1. Enter the URL and select the mode to test.
2. Enter a valid profile count, duration and pause.
3. Click **Create & run new profiles / Tạo & chạy profile mới**.
4. Watch the status, progress and log. Profiles are named `user_001`, `user_002`, …; subsequent creation starts after the highest saved number.

### Reuse saved profiles

1. Click **Refresh / Làm mới** if the list needs updating.
2. Select profiles using Ctrl / Shift, or click **Select all / Chọn tất cả**.
3. Click **Run selected profiles / Chạy profile đã chọn**. Existing cookies and storage are retained; these are not new profiles.

### Stop and close

Click **Stop after current session / Dừng sau phiên hiện tại**. The current session finishes before the tool stops ahead of the next profile. The application blocks closing its window while a run is active. Do not force-terminate the process or open the same profile in multiple tool instances; doing so may cause errors or corrupt profile data.

### Download and GameAnalytics details

- The tool starts a download and requests cancellation immediately; a small file may finish first.
- A new download tab opened by the donation-skip step is supported. Changes to itch.io's interface may still break automation.
- A canceled download is not guaranteed to count in itch.io statistics. Downloading a game does not mean running it or sending GameAnalytics events.
- `ga_requests` only counts observed requests whose URLs contain `gameanalytics`. It does not verify successful responses or event ingestion. This is not an event, session or New User count.
- A new profile does not guarantee a new analytics identity; that depends on how the game/SDK creates and persists identifiers. The game must already integrate analytics to generate its game events when launched.

## Local data and reports

These paths are next to the Python file and are created/saved during use:

| Path | Contents |
| --- | --- |
| `mixie-buff-itch_profiles/` | Reusable profiles; may contain cookies, browsing history and session data. |
| `mixie-buff-itch_reports/` | A CSV report for each run. **Open reports / Mở báo cáo** opens this folder. |
| `mixie-buff-itch_settings.json` | The most recent URL, language and options. Configure these in the UI; no need to create the file manually. |

| CSV column | Meaning |
| --- | --- |
| `timestamp_utc`, `profile`, `profile_reused`, `browser` | UTC session start time, profile name, whether it already contained data, and browser. |
| `status` | `game_iframe_detected`: an iframe was found; `page_opened_no_iframe`: page opened without a detected iframe; `download_cancelled`: cancellation succeeded; `download_completed_before_cancel`: file finished before cancellation; `error`: session failed. An iframe does not prove successful gameplay. |
| `play_action`, `download_action` | Launch attempt result or downloaded filename; may also be `disabled`, `not_started` or `failed`, depending on the flow. |
| `ga_requests`, `ga_hosts` | Count of requests matching the GameAnalytics filter and their hostnames. |
| `iframe_count`, `page_errors` | Iframes observed in game mode; collected page and session errors. |

Open CSV files in a text editor or spreadsheet application. Reports record browser activity observed by the tool; they do not replace itch.io or GameAnalytics dashboards.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| `py` cannot find Python / `No installed Python found` | Try `python --version` and the direct launch method; check your Python and launcher installation. |
| `No module named playwright` | Run `python -m pip install playwright` with the interpreter used to launch the tool. |
| Chromium executable missing | Run `python -m playwright install chromium` with the same interpreter. |
| `tkinter`, `init.tcl`, Tk/Tcl error | Check/repair the Python installation with Tcl/Tk and Tkinter. Try `python -m tkinter` to check whether a Tk window opens. |
| Brave not found | Install Brave in a standard location or select Chromium. |
| Game does not launch / WebGL errors | Disable headless, check the URL and try launching manually in the browser to identify the controls or conditions required by the game. |
| Download button missing / timeout | Check for a free downloadable file, a Download Now button and a supported download flow; inspect `page_errors` in the CSV. |
| Windows reports an unverified publisher | Read the file and verify its source first. For a trusted downloaded ZIP, you can use Properties → Unblock before extracting. |
| Analytics requests appear but dashboard metrics do not increase | Check the game/SDK, analytics project and dashboard data; an observed request does not confirm that the service counted the activity. |

## Educational purpose and responsibility

**This project was created for educational purposes. Do not abuse it. You are responsible for your use of it.**

Only use it with games/systems you own or are authorized to test. Do not use it to cheat rankings, distort commercial metrics or generate unwanted load. Users are responsible for their actions, generated data and compliance with the rules of the services involved. This project does not guarantee metric increases or protection from account limits/restrictions.
