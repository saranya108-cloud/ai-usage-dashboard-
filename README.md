# ai-usage-dashboard
-AI Usage Dashboard

Local dashboard for tracking AI lab activity, model testing, Codex sessions, benchmark results, and project progress.

How to Run

Requires Python 3 (standard library only, nothing to install).

```
python3 app/dashboard.py
```

Then open http://localhost:8000 in your browser. Press Ctrl+C to stop.

Pages:

* / for the main dashboard (summary cards, recent activity, next actions)
* /daily for daily progress
* /models for model comparison (bar chart of average scores, plus a table)
* /usage for the full usage log
* /benchmarks for the full benchmark log

The log pages have clickable filter links (by tool, model, or category).
You can also filter by date in the address bar, for example
/usage?date=2026-06-30.

To add data, either run the helper script:

```
python3 app/add_entry.py
```

which asks a few questions and appends a row to the right CSV file, or
edit the CSV files in data/ directly with any text editor or spreadsheet
app. Then refresh the browser. Field meanings are documented in
docs/requirements.md.

How to Test

Check the code compiles and every page renders:

```
python3 -m py_compile app/dashboard.py
python3 app/dashboard.py &
sleep 1
curl -s http://localhost:8000/ | grep "AI Usage Dashboard"
curl -s http://localhost:8000/daily | grep "Daily progress"
curl -s http://localhost:8000/models | grep "Model comparison"
curl -s http://localhost:8000/usage | grep "Usage log"
curl -s http://localhost:8000/benchmarks | grep "Benchmark log"
kill %1
```

Each grep should print a matching line. Or simply run the server and
click through the five pages in your browser.

Purpose

This repo is a safe, small project for building a local AI usage dashboard.

The dashboard should help track:

* ChatGPT usage
* Claude / Fable usage
* Codex sessions
* Local model tests on the Acer GN100
* Orbit project progress
* Daily progress notes
* Model benchmark results
* Next actions

Current Models and Tools to Track

* ChatGPT
* Claude / Fable
* Codex
* Qwen Coder Next
* GLM-5.2 cloud
* Ornith-1.0

Goals

The first version should include:

1. Dashboard view
2. Daily progress view
3. Model comparison view
4. Simple usage log
5. Simple benchmark log
6. Clear next actions section

Data Fields

Track these fields when useful:

* Date
* Tool or model
* Environment
* Task type
* Task description
* Result
* Score
* Notes
* Next action

Constraints

Keep this project simple.

Rules:

* Do not use npm.
* Do not use pnpm.
* Do not use yarn.
* Do not use bun.
* Do not use npx.
* Do not use pnpx.
* Do not use bunx.
* Do not require cloud services.
* Do not connect to live accounts or APIs in the first version.
* Do not modify files outside this repo.
* Prefer Python standard library when possible.
* Prefer local CSV or JSON files for storage.
* Keep the code easy for a beginner to understand.

First Version

The first version should be local and lightweight.

Preferred structure:

* app/ for dashboard code
* data/ for CSV or JSON files
* docs/ for notes and requirements
* README.md for project overview

Sample Views

The dashboard should eventually include:

Main Dashboard

A simple overview of recent AI usage, model tests, and next actions.

Daily Progress View

A daily log of what was tested, fixed, learned, or completed.

Model Comparison View

A comparison of models such as Qwen Coder Next, GLM-5.2 cloud, and Ornith-1.0.

Useful comparison fields:

* Model name
* Environment
* Task
* Pass or fail
* Score
* Speed
* Reliability
* Notes

Development Rules for AI Assistants

Before changing files, explain the proposed plan and file structure.

After changing files, explain:

* What changed
* Why it changed
* How to run it
* How to test it
* Any known limitations

Do not overbuild the project.

Do not add unnecessary dependencies.

Do not turn this into a complex enterprise app.

The goal is a simple local dashboard that is useful, readable, and maintainable.