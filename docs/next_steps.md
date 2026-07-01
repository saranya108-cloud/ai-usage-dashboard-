# Next steps

Small improvements, in order. Do one at a time and keep each one small.

1. **Weekly summary on the daily view.** Count entries per category per
   week from data already in daily_progress.csv.
2. **Orbit project page.** If Orbit notes outgrow the daily log, give the
   project its own page fed by a data/orbit.csv.

Already done:

* Bar chart on the model comparison view — plain HTML/CSS bars showing
  average benchmark score per model, best first.
* Richer main dashboard — summary cards (including best-scoring and most
  recently tested model) plus recent usage, benchmark, progress, and
  next-action sections.

* Add-entry helper script (`app/add_entry.py`) — answer a few questions
  in the terminal and it appends a row to the right CSV file.
* Filters on the log views — clickable filter rows on /usage (by tool),
  /benchmarks (by model) and /daily (by category), plus a date parameter
  on all three (for example /usage?date=2026-06-30).

Things we decided NOT to do (on purpose):

* No database, no cloud, no login, no live API connections.
* No JavaScript framework and no npm/yarn/bun/etc.
* No config files until something actually needs configuring.
