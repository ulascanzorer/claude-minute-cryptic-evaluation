# Can Claude solve Minute Cryptic offline?

[Minute Cryptic](https://www.minutecryptic.com/) publishes one cryptic crossword clue a day. This repo checks how many of them Claude Opus 5.5 can solve when:

- every clue was published **after the model's training cutoff** (June 2026), so it can't have memorized the answers, and
- Claude has **no tools and no internet**, so it can't look them up.

It runs entirely through [Claude Code](https://claude.com/claude-code) in headless mode, so no API key is needed.

## Results

**Claude Opus 5.5 solved 97 of 111 clues (87.4%)** published between 2026-07-01 and 2026-10-22. That's one attempt per clue at `--effort high`. Three days are missing because the source archive skips them.

A typical clue took about 5 seconds. Every wrong answer still had the right letter count.

### It usually knows when it's wrong

The prompt asks Claude to explain its parse before answering. A simple keyword check for hesitation ("uncertain", "best guess", "couldn't parse", ...) gives this:

| | Hesitated | Confident |
|---|---|---|
| Correct (97) | 5 | 92 |
| Wrong (14) | 13 | 1 |

13 of the 14 wrong answers came with a warning that the parse didn't fully work, compared with 5 of the 97 correct ones.

### Some interesting misses

**Got the letters, lost the answer.**
*After golf, he picked up ball and tee, then left? (5)*. The answer is HOTEL: it comes after Golf in the NATO alphabet, and HE takes in O (ball) and T (tee), then adds L (left). Claude built H(OT)E correctly, then dropped the L, decided the parse "gives HOTE, not HOST", and answered GHOST.

**Didn't play Wordle.**
*Is extremely close to Wordle solve: 🟨🟩🟨🟨🟨 (5)*. The answer is LOVES: the letters of SOLVE with the O green (same spot) and the other four yellow (moved). Claude never tried the letters of "solve". It took the definition as ABUTS and noted that no Wordle pattern fit.

**A confident miss.**
*Cat on a leash locked up without a key (6)*. ATONAL is hidden in "c**at on a l**eash" ("locked up" signals the hidden word), and "without a key" is the definition. Claude answered LASHED with a neat but invented parse ("on a leash" gives LEASHED, minus the key E) and no hesitation at all.

**Missed a simple anagram.**
*It's ok to miscalculate three times two? (5,5)*. The answer is THERE THERE: THREE scrambled, twice. Claude spent two minutes on it and gave up with ABOUT RIGHT.

## How it works

1. **`fetch_puzzles.py`** scrapes every clue from 2026-07-01 to 2026-10-22 (date, clue, answer) from the archive at [linkedinpinpointanswer.today](https://www.linkedinpinpointanswer.today/minute-cryptic-answer-today/archive), since Minute Cryptic's own archive is members-only. The enumeration (word lengths, e.g. `(4,8)`) is computed from the answer.
2. **`solve.py`** sends each clue to Claude with [`prompts/rules.md`](prompts/rules.md) as the system prompt. That prompt explains how cryptic clues work, with one example clue per wordplay type (written by us and checked for correctness), and asks Claude to reply with a `REASONING:` line explaining its parse, followed by an `ANSWER:` line. Claude only sees the clue and its enumeration.
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

`solve.py` doesn't just trust the flags. It reads Claude Code's `init` event and fails if any tool or MCP server is available, or if Claude ever tries a tool call. The full transcript of every attempt is kept in `results/<effort>/raw/`.

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
