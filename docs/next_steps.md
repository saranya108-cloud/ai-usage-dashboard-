# Next steps

Small improvements, in order. Do one at a time and keep each one small.

1. **Add-entry helper script.** A tiny `app/add_entry.py` that asks a few
   questions in the terminal and appends a row to the right CSV file, so
   logging a session does not mean opening a spreadsheet. (This is the
   next planned improvement.)
2. **Filter by tool or date.** Add a simple query parameter (for example
   `/usage?tool=Codex`) so long logs stay readable.
3. **Weekly summary on the daily view.** Count entries per category per
   week from data already in daily_progress.csv.
4. **A tiny bar chart on the model comparison view.** Plain HTML/CSS bars
   for average score, no chart library.
5. **Orbit project page.** If Orbit notes outgrow the daily log, give the
   project its own page fed by a data/orbit.csv.

Things we decided NOT to do (on purpose):

* No database, no cloud, no login, no live API connections.
* No JavaScript framework and no npm/yarn/bun/etc.
* No config files until something actually needs configuring.
