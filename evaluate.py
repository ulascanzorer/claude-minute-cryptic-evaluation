import argparse

import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"], default="high")
results = f"results/{parser.parse_args().effort}"

puzzles = pd.read_json("data/puzzles.jsonl", lines=True, dtype=False)
attempts = pd.read_json(f"{results}/attempts.jsonl", lines=True, dtype=False)
df = puzzles.merge(attempts, on="date", suffixes=("", "_claude"))


def normalize(s: pd.Series) -> pd.Series:
    return s.fillna("").str.upper().str.replace(r"[^A-Z]", "", regex=True)


df["correct"] = normalize(df["answer"]) == normalize(df["answer_claude"])
accuracy = df["correct"].mean()
headline = f"Accuracy: {accuracy:.1%} ({df['correct'].sum()}/{len(df)} clues)"

table = df.assign(clue=df["clue"] + " " + df["enumeration"], correct=df["correct"].map({True: "✓", False: "✗"}))
table = table[["date", "clue", "answer", "answer_claude", "correct"]]

with open(f"{results}/summary.md", "w") as f:
    f.write(f"# Results ({results})\n\n{headline}\n\n{table.to_markdown(index=False)}\n")
print(headline)
