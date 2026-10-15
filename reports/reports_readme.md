

Reports readme · MD
# CodeVibe report: notes from Pauline Moraa
 
This note explains my CodeVibe report (`pauline_report.md`), so it can be read alongside the code and the Git history.
 
## What the report covers
 
- **Tracking started:** 11 Oct 2026, 00:30. My first commit (`d143238`, "filters") followed at 01:23. Tracking started later than the assignment window opened, because [reason, e.g. the team restarted the repository after CodeVibe issues; see the meeting log on the team sheet].
- **Report exported:** 14 Oct 2026, 21:19.
- **Files tracked:** `app.js`, `index.html` and `style.css`. This is the frontend, which was my task on the team sheet.
- **Commit recorded in the report:** the report gives the head commit as `5c42953`. That commit is not in my local history (I checked with `git reflog`) or on GitHub. At the time of the export, my latest commit was `468bb74` ("debugging css", 14 Oct 13:35). I do not know why the report records a different commit.
## AI use
 
- **`index.html` and `style.css`:** the report shows both as reviewed thoroughly.
- **`app.js`:** the report shows it as unreviewed. I reviewed it line by line after the export, while debugging.
## Work done after the export
 
CodeVibe did not record any of this, because the report had already been exported.
 
**14 Oct (minutes after the export):**
 
1. `2715b2e` 21:21: debugging. This commit changed 47 lines of `app.js`, plus `index.html` (12 lines) and `style.css` (31 lines). While debugging, I reviewed `app.js` line by line. I can explain every function in it, including `refresh()`, `zoneStyle()`, `renderTable()` and `selectZone()`.
2. `ccc1398` 21:27: I moved `app.js`, `index.html` and `style.css` from the project root into `frontend/`. That is why the report shows them at the project root.
3. `e70c7be` 21:28: I merged my repository into the team repository (`git pull origin main --allow-unrelated-histories`). My work began in its own repository, so the histories had to be joined.
**15–16 Oct:**
 
| Commit | Time | Change |
|---|---|---|
| `e7da67c` | 15 Oct 21:20 | Algorithm tests |
| `077655e` | 15 Oct 23:03 | Debugged the tests |
| `ff2d6e8` | 15 Oct 23:04 | Added `requirements.txt` |
| `4670fcb` | 15 Oct 23:10 | Edited `requirements.txt` |
| `7b3bcb8` | 16 Oct 00:04 | Added gunicorn for deployment |
| `68acc9c` | 16 Oct 00:24 | Added this CodeVibe report |
 
## My commits before the export (11–14 Oct)
 
| Commit | Time | Change |
|---|---|---|
| `d143238` | 11 Oct 01:23 | Filters |
| `7ea2b29` | 12 Oct 05:20 | HTML file |
| `0de289f` | 12 Oct 05:33 | General website styling |
| `0f93925` | 12 Oct 05:55 | Layout |
| `2cd7575` | 12 Oct 06:11 | Panel and grid styling |
| `329d904` | 12 Oct 06:22 | Responsive layout |
| `c153e1b` | 12 Oct 10:23 | Debugged the HTML file |
| `ea26da7` | 13 Oct 17:13 | Script file (`app.js`) |
| `468bb74` | 14 Oct 13:35 | Debugged the CSS |
 
Claude finished the response
