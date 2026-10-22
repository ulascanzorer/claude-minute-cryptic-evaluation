# Can Claude solve Minute Cryptic offline?

[Minute Cryptic](https://www.minutecryptic.com/) publishes one cryptic crossword clue a day. This repo checks how many of them Claude Opus 5.5 can solve when:

- every clue was published **after the model's training cutoff** (June 2026), so it can't have memorized the answers, and
- Claude has **no tools and no internet**, so it can't look them up.

It runs entirely through [Claude Code](https://claude.com/claude-code) in headless mode, so no API key is needed.

## Results

_Coming soon._

## How it works

1. **`fetch_puzzles.py`** scrapes every clue since 2026-07-01 (date, clue, answer) from the archive at [linkedinpinpointanswer.today](https://www.linkedinpinpointanswer.today/minute-cryptic-answer-today/archive), since Minute Cryptic's own archive is members-only. The enumeration (word lengths, e.g. `(4,8)`) is computed from the answer.
2. **`solve.py`** sends each clue to Claude with [`prompts/rules.md`](prompts/rules.md) as the system prompt. That prompt explains how cryptic clues work and asks for a final `ANSWER: ...` line. Claude only sees the clue and its enumeration.
3. **`evaluate.py`** compares Claude's answers with the real ones, ignoring case, spaces and punctuation.

**Metric:** accuracy, the share of clues answered exactly right. One attempt per clue.

## How Claude is kept offline

Each clue runs as a fresh `claude -p` call in an empty temp directory with:

| Flag | Effect |
|---|---|
| `--tools ""` | no built-in tools at all (no web search, web fetch, shell, or file access) |
| `--strict-mcp-config` | no MCP servers |
| `--safe-mode` | ignores personal CLAUDE.md, plugins, hooks and skills |
| `--disable-slash-commands` | no skills or commands |
| `--system-prompt` | replaces Claude Code's agentic prompt with the rules |

`solve.py` doesn't just trust the flags. It reads Claude Code's `init` event and fails if any tool or MCP server is available, or if Claude ever tries a tool call. The full transcript of every attempt is kept in `results/raw/`.

## Reproduce

Requires [uv](https://docs.astral.sh/uv/) and a logged-in Claude Code.

```sh
uv run fetch_puzzles.py   # -> data/puzzles.jsonl
uv run solve.py           # -> results/high/attempts.jsonl, results/high/raw/ (resumable)
uv run evaluate.py        # -> results/high/summary.md
```

Both scripts take `--effort low|medium|high|xhigh|max` (default `high`), and each level gets its own folder under `results/`. Use `solve.py --limit N` for a quick test run.

## Note on the data

The clues belong to Minute Cryptic. This repo doesn't redistribute them: `data/` and `results/` are gitignored, and you rebuild them by running the scripts. If you like cryptics, go play the daily clue at [minutecryptic.com](https://www.minutecryptic.com/).
