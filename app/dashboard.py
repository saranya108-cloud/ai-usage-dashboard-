"""A simple local AI usage dashboard.

Reads CSV files from the data/ folder and serves a few HTML pages
on http://localhost:8000. Uses only the Python standard library.

Run it with:  python3 app/dashboard.py
Stop it with: Ctrl+C
"""

import csv
import html
from datetime import date
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

PORT = 8000

# The data folder sits next to the app folder, at the repo root.
DATA_DIR = Path(__file__).parent.parent / "data"


# ---------------------------------------------------------------------------
# Reading data
# ---------------------------------------------------------------------------

def read_csv(filename):
    """Read a CSV file from data/ and return a list of row dictionaries."""
    path = DATA_DIR / filename
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# Small HTML helpers
# ---------------------------------------------------------------------------

def esc(text):
    """Escape text so it is safe to put inside HTML."""
    return html.escape(str(text or ""))


def make_table(rows, columns):
    """Build an HTML table.

    `columns` is a list of (csv_field, heading) pairs, so we control
    both the column order and the heading text.
    """
    if not rows:
        return (
            "<p class='empty'>Nothing to show. Add rows to the CSV file in data/, "
            "or clear the filter above if one is active.</p>"
        )
    parts = ["<table><thead><tr>"]
    for _, heading in columns:
        parts.append(f"<th>{esc(heading)}</th>")
    parts.append("</tr></thead><tbody>")
    for row in rows:
        parts.append("<tr>")
        for field, _ in columns:
            parts.append(f"<td>{esc(row.get(field))}</td>")
        parts.append("</tr>")
    parts.append("</tbody></table>")
    return "".join(parts)


def filter_rows(rows, params, allowed):
    """Keep only rows that match the filters in the URL.

    `allowed` maps a URL parameter name to the CSV field it filters,
    e.g. {"tool": "tool", "date": "date"} means ?tool=Codex&date=...
    Matching ignores upper/lower case.
    """
    for param, field in allowed.items():
        wanted = params.get(param)
        if wanted:
            rows = [r for r in rows if (r.get(field) or "").lower() == wanted.lower()]
    return rows


def make_filter_links(base_path, param, values, selected):
    """Build a row of filter links like: Filter: All | Codex | ChatGPT

    The currently selected value is shown in bold instead of as a link.
    """
    links = []
    if selected:
        links.append(f"<a href='{base_path}'>All</a>")
    else:
        links.append("<strong>All</strong>")
    for value in values:
        if selected and value.lower() == selected.lower():
            links.append(f"<strong>{esc(value)}</strong>")
        else:
            href = f"{base_path}?{urlencode({param: value})}"
            links.append(f"<a href='{href}'>{esc(value)}</a>")
    return "<p class='filters'>Filter: " + " | ".join(links) + "</p>"


def text_input(name, placeholder="", required=False):
    """Build one text input for a form."""
    req = " required" if required else ""
    return f"<input name='{name}' placeholder='{esc(placeholder)}'{req}>"


def select_input(name, options):
    """Build a dropdown for a form."""
    opts = "".join(f"<option>{esc(o)}</option>" for o in options)
    return f"<select name='{name}'>{opts}</select>"


def date_input(name):
    """Build a date picker for a form, already set to today."""
    return f"<input type='date' name='{name}' value='{date.today().isoformat()}'>"


def make_form(title, action, rows):
    """Build a small add-entry form.

    `rows` is a list of (label, input_html) pairs. Submitting posts
    to `action`, where do_POST appends the row to the right CSV file.
    """
    fields = "".join(f"<label>{esc(label)}{inp}</label>" for label, inp in rows)
    return (
        f"<h2>{esc(title)}</h2>"
        f"<form method='post' action='{action}' class='entry-form'>"
        + fields
        + "<button type='submit'>Add entry</button></form>"
    )


def make_tile(value, label, small=False):
    """Build one stat tile (a big value with a label under it).

    Use small=True when the value is a name rather than a number,
    so long model names fit inside the tile.
    """
    css = "tile-value small" if small else "tile-value"
    return (
        "<div class='tile'>"
        f"<div class='{css}'>{esc(value)}</div>"
        f"<div class='tile-label'>{esc(label)}</div>"
        "</div>"
    )


def parse_score(value):
    """Return a valid 0-10 score, or None for a blank or invalid value."""
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    return score if 0 <= score <= 10 else None


def average_scores(benchmarks):
    """Return {model name: average score} from rows with valid scores."""
    scores = {}
    for row in benchmarks:
        score = parse_score(row.get("score"))
        if row.get("model") and score is not None:
            scores.setdefault(row["model"], []).append(score)
    return {model: sum(vals) / len(vals) for model, vals in scores.items()}


def make_score_chart(avg_scores):
    """Build a horizontal bar chart of average scores, best first.

    Plain HTML/CSS: each bar is a div whose width is the score as a
    percentage of the 0-10 scale. No JavaScript needed.
    """
    if not avg_scores:
        return "<p class='empty'>No scores yet. Add rows to data/benchmark_log.csv.</p>"
    rows = []
    for model, score in sorted(avg_scores.items(), key=lambda item: item[1], reverse=True):
        percent = score / 10 * 100
        rows.append(
            "<div class='chart-row'>"
            f"<div class='chart-label'>{esc(model)}</div>"
            f"<div class='chart-track'>"
            f"<div class='chart-bar' style='width:{percent:.0f}%'></div>"
            f"<span class='chart-value'>{score:.1f}</span>"
            "</div></div>"
        )
    return "<div class='chart'>" + "".join(rows) + "</div>"


def make_page(title, body):
    """Wrap page content in the shared layout (nav bar + styles)."""
    nav_links = [
        ("/", "Dashboard"),
        ("/daily", "Daily progress"),
        ("/models", "Model comparison"),
        ("/usage", "Usage log"),
        ("/benchmarks", "Benchmark log"),
    ]
    nav = "".join(
        f"<a href='{href}'>{esc(text)}</a>" for href, text in nav_links
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} - AI Usage Dashboard</title>
<style>
  :root {{
    --page: #f9f9f7;
    --surface: #fcfcfb;
    --ink: #0b0b0b;
    --ink-2: #52514e;
    --muted: #898781;
    --line: #e1e0d9;
    --baseline: #c3c2b7;
    --bar: #2a78d6;
    --good: #006300;
    --bad: #d03b3b;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --page: #0d0d0d;
      --surface: #1a1a19;
      --ink: #ffffff;
      --ink-2: #c3c2b7;
      --muted: #898781;
      --line: #2c2c2a;
      --baseline: #383835;
      --bar: #3987e5;
      --good: #0ca30c;
      --bad: #e66767;
    }}
  }}
  body {{
    margin: 0;
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
    background: var(--page);
    color: var(--ink);
  }}
  header {{
    padding: 16px 24px;
    border-bottom: 1px solid var(--line);
    background: var(--surface);
  }}
  header h1 {{ margin: 0 0 8px; font-size: 20px; }}
  nav a {{
    margin-right: 16px;
    color: var(--ink-2);
    text-decoration: none;
    font-size: 14px;
  }}
  nav a:hover {{ color: var(--ink); text-decoration: underline; }}
  main {{ padding: 24px; max-width: 960px; margin: 0 auto; }}
  h2 {{ font-size: 16px; margin: 32px 0 12px; }}
  h2:first-child {{ margin-top: 0; }}
  .tiles {{ display: flex; flex-wrap: wrap; gap: 12px; }}
  .tile {{
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 16px 20px;
    min-width: 130px;
  }}
  .tile-value {{ font-size: 28px; font-weight: 600; }}
  .tile-value.small {{ font-size: 18px; padding: 5px 0; }}
  .tile-label {{ font-size: 13px; color: var(--ink-2); margin-top: 4px; }}
  .chart {{ display: grid; gap: 8px; margin: 12px 0 8px; }}
  .chart-row {{ display: flex; align-items: center; gap: 10px; font-size: 14px; }}
  .chart-label {{ width: 160px; text-align: right; color: var(--ink-2); flex-shrink: 0; }}
  .chart-track {{
    flex: 1; display: flex; align-items: center; gap: 8px;
    border-left: 2px solid var(--baseline);
  }}
  .chart-bar {{ height: 18px; background: var(--bar); border-radius: 0 4px 4px 0; }}
  .chart-value {{ font-variant-numeric: tabular-nums; }}
  table {{
    border-collapse: collapse;
    width: 100%;
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 8px;
    font-size: 14px;
  }}
  th, td {{
    text-align: left;
    padding: 8px 12px;
    border-bottom: 1px solid var(--line);
    vertical-align: top;
  }}
  th {{ color: var(--muted); font-weight: 600; font-size: 12px; }}
  td.num {{ font-variant-numeric: tabular-nums; }}
  tr:last-child td {{ border-bottom: none; }}
  .pass {{ color: var(--good); font-weight: 600; }}
  .fail {{ color: var(--bad); font-weight: 600; }}
  .done {{ color: var(--muted); text-decoration: line-through; }}
  .empty {{ color: var(--muted); }}
  .filters {{ font-size: 14px; color: var(--ink-2); }}
  .filters a {{ color: var(--ink-2); }}
  .entry-form {{
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 16px;
    display: grid;
    gap: 10px;
    max-width: 480px;
    font-size: 14px;
  }}
  .entry-form label {{ display: grid; gap: 4px; color: var(--ink-2); }}
  .entry-form input, .entry-form select {{
    padding: 6px 8px;
    border: 1px solid var(--line);
    border-radius: 4px;
    background: var(--page);
    color: var(--ink);
    font: inherit;
  }}
  .entry-form button {{
    justify-self: start;
    padding: 8px 16px;
    border: none;
    border-radius: 6px;
    background: var(--bar);
    color: #ffffff;
    font: inherit;
    cursor: pointer;
  }}
  footer {{ padding: 24px; color: var(--muted); font-size: 12px; text-align: center; }}
</style>
</head>
<body>
<header>
  <h1>AI Usage Dashboard</h1>
  <nav>{nav}</nav>
</header>
<main>
{body}
</main>
<footer>Data lives in the data/ folder. Add entries with the form on each page, or edit the CSV files directly.</footer>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

USAGE_COLUMNS = [
    ("date", "Date"),
    ("tool", "Tool / model"),
    ("environment", "Environment"),
    ("task_type", "Task type"),
    ("description", "Description"),
    ("result", "Result"),
    ("notes", "Notes"),
]

BENCHMARK_COLUMNS = [
    ("date", "Date"),
    ("model", "Model"),
    ("environment", "Environment"),
    ("task", "Task"),
    ("pass_fail", "Pass / fail"),
    ("score", "Score (0-10)"),
    ("speed", "Speed"),
    ("reliability", "Reliability"),
    ("notes", "Notes"),
]

PROGRESS_COLUMNS = [
    ("date", "Date"),
    ("category", "Category"),
    ("note", "Note"),
    ("next_action", "Next action"),
]


def next_actions_list(limit=None):
    """Build the next actions list, open items first, done items last.

    Pass a limit to show only the first few (used on the main dashboard).
    """
    actions = read_csv("next_actions.csv")
    if not actions:
        return "<p class='empty'>No next actions yet. Add rows to data/next_actions.csv.</p>"
    def numeric_priority(action):
        try:
            return int(action.get("priority", ""))
        except (TypeError, ValueError):
            return float("inf")

    actions.sort(key=lambda a: (a.get("status") == "done", numeric_priority(a)))
    total = len(actions)
    if limit:
        actions = actions[:limit]
    items = []
    for a in actions:
        css = " class='done'" if a.get("status") == "done" else ""
        items.append(f"<li{css}>{esc(a.get('action'))}</li>")
    note = ""
    if limit and total > limit:
        note = (
            f"<p class='empty'>Showing the top {limit} of {total} actions. "
            "The full list is in data/next_actions.csv.</p>"
        )
    return "<ol>" + "".join(items) + "</ol>" + note


def dashboard_page(params):
    """The main overview: stat tiles, recent activity, next actions."""
    usage = read_csv("usage_log.csv")
    benchmarks = read_csv("benchmark_log.csv")
    progress = read_csv("daily_progress.csv")
    actions = read_csv("next_actions.csv")

    open_actions = [a for a in actions if a.get("status") != "done"]

    # Best-scoring model = highest average score in the benchmark log.
    avg = average_scores(benchmarks)
    best_model = max(avg, key=avg.get) if avg else "none yet"

    # Most recent model tested = the model on the newest benchmark row.
    if benchmarks:
        latest_model = max(benchmarks, key=lambda r: r.get("date", "")).get("model", "?")
    else:
        latest_model = "none yet"

    tiles = (
        make_tile(len(usage), "usage entries")
        + make_tile(len(benchmarks), "benchmark tests")
        + make_tile(best_model, "best-scoring model", small=True)
        + make_tile(latest_model, "most recent model tested", small=True)
        + make_tile(len(open_actions), "open next actions")
    )

    # Show the most recent entries first (the CSVs are oldest-first).
    recent_usage = sorted(usage, key=lambda r: r.get("date", ""), reverse=True)[:5]
    recent_benchmarks = sorted(benchmarks, key=lambda r: r.get("date", ""), reverse=True)[:5]
    recent_progress = sorted(progress, key=lambda r: r.get("date", ""), reverse=True)[:3]

    body = (
        "<h2>Overview</h2>"
        f"<div class='tiles'>{tiles}</div>"
        "<h2>Recent usage</h2>"
        + make_table(recent_usage, USAGE_COLUMNS)
        + "<h2>Recent benchmarks</h2>"
        + make_table(recent_benchmarks, BENCHMARK_COLUMNS)
        + "<h2>Recent daily progress</h2>"
        + make_table(recent_progress, PROGRESS_COLUMNS)
        + "<h2>Next actions</h2>"
        + next_actions_list(limit=5)
        + make_form("Add a next action", "/add-action", [
            ("Action", text_input("action", "The thing to do", required=True)),
            ("Priority (leave blank for next number)", text_input("priority", "1 = most important")),
            ("Status", select_input("status", ["open", "done"])),
        ])
    )
    return make_page("Dashboard", body)


def daily_page(params):
    """Daily progress notes, newest day first. Filter with ?category= or ?date=."""
    progress = read_csv("daily_progress.csv")
    categories = sorted({r.get("category", "") for r in progress if r.get("category")})
    rows = filter_rows(progress, params, {"category": "category", "date": "date"})
    rows.sort(key=lambda r: r.get("date", ""), reverse=True)
    body = (
        "<h2>Daily progress</h2>"
        + make_filter_links("/daily", "category", categories, params.get("category"))
        + make_table(rows, PROGRESS_COLUMNS)
        + make_form("Add a progress note", "/add-progress", [
            ("Date", date_input("date")),
            ("Category", select_input("category", ["tested", "fixed", "learned", "completed"])),
            ("Note", text_input("note", "What happened", required=True)),
            ("Next action", text_input("next_action", "Optional")),
        ])
    )
    return make_page("Daily progress", body)


def models_page(params):
    """Compare models using the benchmark log: pass rate and average score."""
    benchmarks = read_csv("benchmark_log.csv")

    # Group benchmark rows by model name.
    by_model = {}
    for row in benchmarks:
        by_model.setdefault(row.get("model", "unknown"), []).append(row)

    parts = ["<h2>Average benchmark score by model (0-10)</h2>"]
    parts.append(make_score_chart(average_scores(benchmarks)))
    parts.append("<h2>Model comparison</h2>")
    if not by_model:
        parts.append("<p class='empty'>No benchmarks yet. Add rows to data/benchmark_log.csv.</p>")
    else:
        parts.append(
            "<table><thead><tr>"
            "<th>Model</th><th>Environments</th><th>Runs</th><th>Passed</th>"
            "<th>Pass rate</th><th>Avg score</th><th>Latest note</th>"
            "</tr></thead><tbody>"
        )
        for model in sorted(by_model):
            runs = by_model[model]
            passed = sum(1 for r in runs if r.get("pass_fail") == "pass")
            scores = []
            for run in runs:
                score = parse_score(run.get("score"))
                if score is not None:
                    scores.append(score)
            avg_score = sum(scores) / len(scores) if scores else 0
            envs = sorted({r.get("environment", "") for r in runs})
            latest = max(runs, key=lambda r: r.get("date", ""))
            pass_css = "pass" if passed == len(runs) else ""
            parts.append(
                "<tr>"
                f"<td>{esc(model)}</td>"
                f"<td>{esc(', '.join(envs))}</td>"
                f"<td class='num'>{len(runs)}</td>"
                f"<td class='num'>{passed}</td>"
                f"<td class='num {pass_css}'>{passed / len(runs):.0%}</td>"
                f"<td class='num'>{avg_score:.1f}</td>"
                f"<td>{esc(latest.get('notes'))}</td>"
                "</tr>"
            )
        parts.append("</tbody></table>")
        parts.append(
            "<p class='empty'>Numbers come from data/benchmark_log.csv. "
            "See the <a href='/benchmarks'>full benchmark log</a> for every run.</p>"
        )
    return make_page("Model comparison", "".join(parts))


def usage_page(params):
    """The usage log, newest first. Filter with ?tool= or ?date=."""
    usage = read_csv("usage_log.csv")
    tools = sorted({r.get("tool", "") for r in usage if r.get("tool")})
    rows = filter_rows(usage, params, {"tool": "tool", "date": "date"})
    rows.sort(key=lambda r: r.get("date", ""), reverse=True)
    body = (
        "<h2>Usage log</h2>"
        + make_filter_links("/usage", "tool", tools, params.get("tool"))
        + make_table(rows, USAGE_COLUMNS)
        + make_form("Add a usage entry", "/add-usage", [
            ("Date", date_input("date")),
            ("Tool or model", text_input("tool", "e.g. ChatGPT, Qwen Coder Next", required=True)),
            ("Environment", text_input("environment", "e.g. browser, terminal, Acer GN100", required=True)),
            ("Task type", text_input("task_type", "e.g. coding, research, summarize", required=True)),
            ("Description", text_input("description", "What you did", required=True)),
            ("Result", select_input("result", ["good", "ok", "bad"])),
            ("Notes", text_input("notes", "Optional")),
        ])
    )
    return make_page("Usage log", body)


def benchmarks_page(params):
    """The benchmark log, newest first. Filter with ?model= or ?date=."""
    benchmarks = read_csv("benchmark_log.csv")
    models = sorted({r.get("model", "") for r in benchmarks if r.get("model")})
    rows = filter_rows(benchmarks, params, {"model": "model", "date": "date"})
    rows.sort(key=lambda r: r.get("date", ""), reverse=True)
    body = (
        "<h2>Benchmark log</h2>"
        + make_filter_links("/benchmarks", "model", models, params.get("model"))
        + make_table(rows, BENCHMARK_COLUMNS)
        + make_form("Add a benchmark", "/add-benchmark", [
            ("Date", date_input("date")),
            ("Model", text_input("model", "e.g. Ornith-1.0", required=True)),
            ("Environment", text_input("environment", "e.g. Acer GN100", required=True)),
            ("Task", text_input("task", "What was tested", required=True)),
            ("Pass or fail", select_input("pass_fail", ["pass", "fail"])),
            ("Score (0-10)", "<input type='number' name='score' min='0' max='10' required>"),
            ("Speed", select_input("speed", ["fast", "medium", "slow"])),
            ("Reliability", select_input("reliability", ["high", "medium", "low"])),
            ("Notes", text_input("notes", "Optional")),
        ])
    )
    return make_page("Benchmark log", body)


# ---------------------------------------------------------------------------
# The web server
# ---------------------------------------------------------------------------

PAGES = {
    "/": dashboard_page,
    "/daily": daily_page,
    "/models": models_page,
    "/usage": usage_page,
    "/benchmarks": benchmarks_page,
}

# For each form: which CSV file to append to, the column order,
# and which page to send the browser back to afterwards.
FORMS = {
    "/add-usage": ("usage_log.csv", ["date", "tool", "environment", "task_type", "description", "result", "notes"], "/usage"),
    "/add-benchmark": ("benchmark_log.csv", ["date", "model", "environment", "task", "pass_fail", "score", "speed", "reliability", "notes"], "/benchmarks"),
    "/add-progress": ("daily_progress.csv", ["date", "category", "note", "next_action"], "/daily"),
    "/add-action": ("next_actions.csv", ["priority", "action", "status"], "/"),
}


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Split "/usage?tool=Codex" into the path and the filter parameters.
        url = urlparse(self.path)
        page = PAGES.get(url.path)
        if page is None:
            self.send_error(404, "Page not found")
            return
        params = {name: values[0] for name, values in parse_qs(url.query).items()}
        content = page(params).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        form = FORMS.get(self.path)
        if form is None:
            self.send_error(404, "Unknown form")
            return
        filename, fields, back_to = form

        # The form data arrives in the request body, URL-encoded.
        length = int(self.headers.get("Content-Length", 0))
        submitted = parse_qs(self.rfile.read(length).decode("utf-8"))
        row = [submitted.get(field, [""])[0].strip() for field in fields]

        # Same defaults as the terminal helper: today's date, and the
        # next free priority number for next actions.
        if "date" in fields and not row[fields.index("date")]:
            row[fields.index("date")] = date.today().isoformat()
        if "priority" in fields and not row[fields.index("priority")]:
            priorities = []
            for existing in read_csv(filename):
                try:
                    priorities.append(int(existing.get("priority", "")))
                except (TypeError, ValueError):
                    pass
            row[fields.index("priority")] = str(max(priorities, default=0) + 1)

        with open(DATA_DIR / filename, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(row)

        # Redirect back, so refreshing the page does not re-submit.
        self.send_response(303)
        self.send_header("Location", back_to)
        self.end_headers()

    def log_message(self, format, *args):
        pass  # keep the terminal quiet while browsing


def main():
    server = HTTPServer(("localhost", PORT), DashboardHandler)
    print(f"AI Usage Dashboard running at http://localhost:{PORT}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
