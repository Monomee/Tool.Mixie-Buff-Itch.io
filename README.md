# mixie-buff-itch

itch.io WebGL QA Tester
Windows 10/11, Python 3.10+ (with Tkinter) required.

Python module names use underscores: `mixie_buff_itch.py`.
Local browser profiles, reports, settings, and logs are excluded from Git by `.gitignore`.
Settings and data folders are created automatically when the app runs.
Use the Language / Ngôn ngữ selector at the top right to switch between Tiếng Việt and English immediately. The choice is saved for the next launch; existing log entries and CSV status codes stay unchanged.

1) Extract all files to one folder.
2) Double-click INSTALL_MIXIE_BUFF_ITCH.bat once (internet connection required).
3) Double-click RUN_MIXIE_BUFF_ITCH.bat.
4) Keep the preset Mixie Empire itch.io URL or change it to another itch.io test URL.
5) Choose Chromium or Brave, 1-100 new profiles, duration, inter-session gap, auto-play, mute, and click 'Tao & chay profile MOI'.
6) For a returning-user test, select profiles in the list and click 'Chay profile da chon'.
7) The GUI writes reusable profiles to mixie-buff-itch_profiles/ and per-run CSV reports to mixie-buff-itch_reports/.

Download mode:
- Check 'Download roi huy file (thay cho chay game)' to run the download flow instead of the game.
- Use 'Chay profile da chon' to reuse an existing profile; creating a new profile is optional.
- Each selected profile clicks Download Now, skips the optional donation screen, clicks the first visible file download, then cancels it.
- If skipping the donation opens a new download tab (HTML/WebGL games), the tool follows that tab automatically.
- Game duration and Auto Play are ignored in this mode; the inter-session gap still applies.
- Paid-only pages or missing download buttons fail the session without submitting a payment.
- CSV status is download_cancelled, download_completed_before_cancel (a small file finished first), or error. The download_action column records the filename when successful.
- These results confirm browser activity only, not an increase in itch.io download statistics or protection from account restrictions.
- Download mode is off by default and is saved with the other settings. Uncheck it to return to game testing.

Notes:
- Use a dedicated GameAnalytics TEST game/project or test key to avoid polluting production metrics.
- GameAnalytics event requests do not guarantee New User counting; confirm in the GameAnalytics dashboard after processing.
- 'Auto Play' is best-effort and might need updating if itch.io changes its page UI.
- Playback is sequential, not concurrent. Stop finishes the current session before exiting.
- Closing the app while a test is running is disabled to prevent corrupting browser profiles.
- Brave is automatically looked up in common Windows install locations.
- Disabling sound with --mute-audio mutes browser output; it doesn't affect the game's internal audio state.
- Playwright Chromium installed via INSTALL is separate from the user's Brave installation.
