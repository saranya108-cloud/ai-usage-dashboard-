"""A simple local AI usage dashboard.

Reads CSV files from the data/ folder and serves a few HTML pages
on http://localhost:8000. Uses only the Python standard library.

Run it with:  python3 app/dashboard.py
Stop it with: Ctrl+C
"""

import csv
import html
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

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
        return "<p class='empty'>No entries yet. Add rows to the CSV file in data/.</p>"
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


def make_tile(value, label):
    """Build one stat tile (a big number with a label under it)."""
    return (
        "<div class='tile'>"
        f"<div class='tile-value'>{esc(value)}</div>"
        f"<div class='tile-label'>{esc(label)}</div>"
        "</div>"
    )


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
  .tile-label {{ font-size: 13px; color: var(--ink-2); margin-top: 4px; }}
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
<footer>Data lives in the data/ folder. Edit the CSV files and refresh.</footer>
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


def next_actions_list():
    """Build the next actions list, open items first."""
    actions = read_csv("next_actions.csv")
    if not actions:
        return "<p class='empty'>No next actions yet. Add rows to data/next_actions.csv.</p>"
    actions.sort(key=lambda a: (a.get("status") == "done", a.get("priority", "")))
    items = []
    for a in actions:
        css = " class='done'" if a.get("status") == "done" else ""
        items.append(f"<li{css}>{esc(a.get('action'))}</li>")
    return "<ol>" + "".join(items) + "</ol>"


def dashboard_page():
    """The main overview: stat tiles, recent activity, next actions."""
    usage = read_csv("usage_log.csv")
    benchmarks = read_csv("benchmark_log.csv")
    progress = read_csv("daily_progress.csv")
    actions = read_csv("next_actions.csv")

    models = sorted({row["tool"] for row in usage if row.get("tool")})
    open_actions = [a for a in actions if a.get("status") != "done"]

    tiles = (
        make_tile(len(usage), "usage entries")
        + make_tile(len(benchmarks), "benchmark runs")
        + make_tile(len(models), "tools tracked")
        + make_tile(len(open_actions), "open next actions")
    )

    # Show the most recent entries first (the CSVs are oldest-first).
    recent_usage = sorted(usage, key=lambda r: r.get("date", ""), reverse=True)[:5]
    recent_progress = sorted(progress, key=lambda r: r.get("date", ""), reverse=True)[:3]

    body = (
        "<h2>Overview</h2>"
        f"<div class='tiles'>{tiles}</div>"
        "<h2>Recent usage</h2>"
        + make_table(recent_usage, USAGE_COLUMNS)
        + "<h2>Recent daily progress</h2>"
        + make_table(recent_progress, PROGRESS_COLUMNS)
        + "<h2>Next actions</h2>"
        + next_actions_list()
    )
    return make_page("Dashboard", body)


def daily_page():
    """Daily progress notes, newest day first."""
    progress = read_csv("daily_progress.csv")
    progress.sort(key=lambda r: r.get("date", ""), reverse=True)
    body = "<h2>Daily progress</h2>" + make_table(progress, PROGRESS_COLUMNS)
    return make_page("Daily progress", body)


def models_page():
    """Compare models using the benchmark log: pass rate and average score."""
    benchmarks = read_csv("benchmark_log.csv")

    # Group benchmark rows by model name.
    by_model = {}
    for row in benchmarks:
        by_model.setdefault(row.get("model", "unknown"), []).append(row)

    parts = ["<h2>Model comparison</h2>"]
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
            scores = [float(r["score"]) for r in runs if r.get("score")]
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


def usage_page():
    """The full usage log, newest first."""
    usage = read_csv("usage_log.csv")
    usage.sort(key=lambda r: r.get("date", ""), reverse=True)
    body = "<h2>Usage log</h2>" + make_table(usage, USAGE_COLUMNS)
    return make_page("Usage log", body)


def benchmarks_page():
    """The full benchmark log, newest first."""
    benchmarks = read_csv("benchmark_log.csv")
    benchmarks.sort(key=lambda r: r.get("date", ""), reverse=True)
    body = "<h2>Benchmark log</h2>" + make_table(benchmarks, BENCHMARK_COLUMNS)
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


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        page = PAGES.get(self.path)
        if page is None:
            self.send_error(404, "Page not found")
            return
        content = page().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

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
