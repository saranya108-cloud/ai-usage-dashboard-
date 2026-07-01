"""Add an entry to one of the data CSV files by answering questions.

Run it with:  python3 app/add_entry.py

It asks which log you want to add to, asks one question per field,
and appends a single row to the matching CSV file in data/.
Uses only the Python standard library.
"""

import csv
from datetime import date
from pathlib import Path

# The data folder sits next to the app folder, at the repo root.
DATA_DIR = Path(__file__).parent.parent / "data"


def ask(question, default=""):
    """Ask one question and return the answer.

    If a default is given, pressing Enter accepts it.
    If there is no default, keep asking until something is typed.
    """
    if default:
        answer = input(f"{question} [{default}]: ").strip()
        return answer or default
    while True:
        answer = input(f"{question}: ").strip()
        if answer:
            return answer
        print("  Please type something.")


def ask_optional(question):
    """Ask one question where an empty answer is fine."""
    return input(f"{question} (optional): ").strip()


def append_row(filename, row):
    """Append one row (a list of values) to a CSV file in data/."""
    path = DATA_DIR / filename
    with open(path, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(row)
    print(f"\nAdded to {path}. Refresh the dashboard to see it.")


def add_usage():
    today = date.today().isoformat()
    row = [
        ask("Date (YYYY-MM-DD)", default=today),
        ask("Tool or model (e.g. ChatGPT, Qwen Coder Next)"),
        ask("Environment (e.g. browser, terminal, Acer GN100)"),
        ask("Task type (e.g. coding, research, summarize)"),
        ask("Description (what you did)"),
        ask("Result (good / ok / bad)"),
        ask_optional("Notes"),
    ]
    append_row("usage_log.csv", row)


def add_benchmark():
    today = date.today().isoformat()
    row = [
        ask("Date (YYYY-MM-DD)", default=today),
        ask("Model (e.g. Ornith-1.0)"),
        ask("Environment (e.g. Acer GN100)"),
        ask("Task (what was tested)"),
        ask("Pass or fail (pass / fail)"),
        ask("Score (0-10)"),
        ask("Speed (fast / medium / slow)"),
        ask("Reliability (high / medium / low)"),
        ask_optional("Notes"),
    ]
    append_row("benchmark_log.csv", row)


def add_progress():
    today = date.today().isoformat()
    row = [
        ask("Date (YYYY-MM-DD)", default=today),
        ask("Category (tested / fixed / learned / completed)"),
        ask("Note (what happened)"),
        ask_optional("Next action"),
    ]
    append_row("daily_progress.csv", row)


def add_next_action():
    # Suggest the next free priority number based on how many rows exist.
    with open(DATA_DIR / "next_actions.csv", newline="", encoding="utf-8") as f:
        existing = list(csv.DictReader(f))
    row = [
        ask("Priority (1 = most important)", default=str(len(existing) + 1)),
        ask("Action (the thing to do)"),
        ask("Status (open / done)", default="open"),
    ]
    append_row("next_actions.csv", row)


def main():
    print("Which log do you want to add to?")
    print("  1. Usage log")
    print("  2. Benchmark log")
    print("  3. Daily progress")
    print("  4. Next actions")
    choices = {"1": add_usage, "2": add_benchmark, "3": add_progress, "4": add_next_action}
    choice = ask("Enter 1, 2, 3 or 4")
    if choice not in choices:
        print("Unknown choice, nothing added.")
        return
    print()  # blank line before the questions
    choices[choice]()


if __name__ == "__main__":
    main()
