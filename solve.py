import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path

from tqdm import tqdm

MODEL = "claude-opus-5-5"
PUZZLES = Path("data/puzzles.jsonl")
EFFORTS = ["low", "medium", "high", "xhigh", "max"]
SYSTEM_PROMPT = Path("prompts/rules.md").read_text()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def ask_claude(clue: str, enumeration: str, effort: str) -> list[dict]:
    cmd = [
        "claude", "-p", f"Clue: {clue} {enumeration}",
        "--model", MODEL,
        "--effort", effort,
        "--system-prompt", SYSTEM_PROMPT,
        "--tools", "",
        "--strict-mcp-config",
        "--safe-mode",
        "--disable-slash-commands",
        "--no-session-persistence",
        "--output-format", "stream-json", "--verbose",
    ]
    # An empty cwd means there is no project context Claude could pick up.
    with tempfile.TemporaryDirectory() as cwd:
        out = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True).stdout
    return [json.loads(line) for line in out.splitlines() if line.strip()]


def check_isolation(events: list[dict]) -> None:
    init = next(e for e in events if e.get("type") == "system" and e.get("subtype") == "init")
    assert init["tools"] == [], f"Claude had tools: {init['tools']}"
    assert init["mcp_servers"] == [], f"Claude had MCP servers: {init['mcp_servers']}"
    for e in events:
        if e.get("type") == "assistant":
            assert all(b.get("type") != "tool_use" for b in e["message"]["content"]), "Claude used a tool"


def parse_answer(events: list[dict]) -> str | None:
    result = next(e for e in events if e.get("type") == "result")["result"]
    matches = re.findall(r"^\W*ANSWER:\s*(.+)$", result, re.MULTILINE)
    return matches[-1].strip() if matches else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--effort", choices=EFFORTS, default="high")
    parser.add_argument("--limit", type=int, help="only solve the first N unsolved puzzles")
    args = parser.parse_args()

    results = Path("results") / args.effort
    attempts = results / "attempts.jsonl"
    raw = results / "raw"
    done = {a["date"] for a in read_jsonl(attempts)}
    todo = [p for p in read_jsonl(PUZZLES) if p["date"] not in done][: args.limit]
    raw.mkdir(parents=True, exist_ok=True)

    for puzzle in tqdm(todo):
        events = ask_claude(puzzle["clue"], puzzle["enumeration"], args.effort)
        (raw / f"{puzzle['date']}.jsonl").write_text("\n".join(json.dumps(e) for e in events) + "\n")
        check_isolation(events)
        with attempts.open("a") as f:
            f.write(json.dumps({"date": puzzle["date"], "answer": parse_answer(events)}) + "\n")


if __name__ == "__main__":
    main()
