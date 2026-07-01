# Notes and requirements

Short reference for how this project stores data and why. The full project
overview lives in the top-level README.md.

## How it works

- `app/dashboard.py` is a small local web server (Python standard library only).
- It reads the CSV files in `data/` and renders five HTML pages.
- There is no database, no cloud service, and no live API connection.
- To add data, edit the CSV files with any text editor or spreadsheet app,
  then refresh the browser.

## Data formats

All files live in `data/` and have one header row.

### usage_log.csv

One row per AI tool session.

| Field | Meaning | Example |
|---|---|---|
| date | ISO date, YYYY-MM-DD | 2026-06-30 |
| tool | Tool or model name | Qwen Coder Next |
| environment | Where it ran | Acer GN100, browser, terminal |
| task_type | Short category | coding, research, summarize |
| description | What you did | Local test: write unit tests |
| result | good / ok / bad | good |
| notes | Anything worth remembering | Best local result so far |

### benchmark_log.csv

One row per model test run.

| Field | Meaning | Example |
|---|---|---|
| date | ISO date | 2026-06-30 |
| model | Model name | Ornith-1.0 |
| environment | Where it ran | Acer GN100 |
| task | What was tested | Explain a regex pattern |
| pass_fail | pass or fail | pass |
| score | 0-10, your judgement | 7 |
| speed | fast / medium / slow | slow |
| reliability | high / medium / low | medium |
| notes | Anything worth remembering | Correct but verbose |

### daily_progress.csv

One row per progress note. A day can have several rows.

| Field | Meaning |
|---|---|
| date | ISO date |
| category | tested, fixed, learned, or completed |
| note | The progress note itself |
| next_action | What to do next about it (optional) |

### next_actions.csv

Your running to-do list.

| Field | Meaning |
|---|---|
| priority | 1 = most important |
| action | The thing to do |
| status | open or done |

## Conventions

- Dates are always `YYYY-MM-DD` so plain text sorting works.
- Model names should match between files (e.g. always "Qwen Coder Next")
  so the model comparison view groups them correctly.
- Keep notes short; this is a log, not a diary.

## Decisions made

- CSV over JSON: easier to edit by hand and opens in any spreadsheet app.
- One Python file: easiest to read top to bottom for a beginner.
- No add-entry script in v1: editing the CSV directly is simple enough.
  A small helper script is the planned next improvement.
