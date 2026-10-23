import json
import time
from datetime import date, datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ARCHIVE_URL = "https://www.linkedinpinpointanswer.today/minute-cryptic-answer-today/archive"
CUTOFF = date(2026, 7, 1)  # Opus 5.5 training cutoff is June 2026
END = date(2026, 10, 22)  # fixed so reruns fetch the same set
OUT = Path("data/puzzles.jsonl")


def enumeration(answer: str) -> str:
    words = answer.split()
    return "(" + ",".join("-".join(str(len(p)) for p in w.split("-")) for w in words) + ")"


def fetch_page(page: int) -> list[dict]:
    html = requests.get(ARCHIVE_URL, params={"page": page}, headers={"User-Agent": "Mozilla/5.0"}, timeout=30).text
    rows = BeautifulSoup(html, "html.parser").select("table tbody tr")
    puzzles = []
    for row in rows:
        day, _, clue, answer = (td.get_text(" ", strip=True) for td in row.find_all("td"))
        puzzles.append({
            "date": datetime.strptime(day, "%b %d, %Y").date().isoformat(),
            "clue": clue,
            "enumeration": enumeration(answer),
            "answer": answer,
        })
    return puzzles


def main():
    puzzles = {}
    page = 1
    while True:
        rows = fetch_page(page)
        dates = [date.fromisoformat(p["date"]) for p in rows]
        puzzles.update({p["date"]: p for p, d in zip(rows, dates) if CUTOFF <= d <= END})
        if not rows or min(dates) < CUTOFF:
            break
        page += 1
        time.sleep(1)

    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w") as f:
        for d in sorted(puzzles):
            f.write(json.dumps(puzzles[d], ensure_ascii=False) + "\n")
    dates = sorted(puzzles)
    print(f"Saved {len(dates)} puzzles ({dates[0]} to {dates[-1]}) to {OUT}")


if __name__ == "__main__":
    main()
