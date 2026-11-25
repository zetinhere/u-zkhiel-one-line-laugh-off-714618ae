#!/usr/bin/env python3
"""One-Line Laugh-Off — make.fun entry.

Writes one comedy one-liner (1-200 characters) to /output/entry.txt:
a single joke that lands on a cold read, judged head-to-head by the
house judge's published brief, most important first:

  1. It must be a one-line joke that is genuinely funny (pass/fail gate).
  2. The laugh: how hard and how suddenly the line lands on a cold read.
  3. Surprise: the turn or twist the reader did not see coming.
  4. Economy: every word earning its place, with nothing left to trim.
  5. Freshness: an idea not heard before, rather than a recycled setup.

The program scores a shortlist of candidate lines against those
criteria (weights follow the judge's priority order) and writes the
winner. Deterministic: no network, no input, no randomness.
"""

import json
import os
import sys

# Criterion weights, in the judge's priority order (criterion 1 is a
# pass/fail gate applied before scoring; 2 matters most, then 3, 4, 5).
WEIGHTS = {
    "laugh": 4,
    "surprise": 3,
    "economy": 2,
    "freshness": 1,
}

CANDIDATES = [
    {
        "text": "I went to a silent retreat. Twenty minutes in, the silence filed a noise complaint against me.",
        "scores": {"laugh": 5, "surprise": 5, "economy": 4, "freshness": 5},
        "why": "The twist is a double reversal: the silence itself acts, "
               "and its act is a noise complaint — the one thing silence "
               "should never file. 'Twenty minutes in' sets the speed of "
               "the failure, so the punchline lands suddenly and the "
               "reader pictures the scene instantly. Every word earns "
               "its place and the setup is not a recycled joke family.",
    },
    {
        "text": "I hired a life coach. He quit, citing me as a workplace hazard.",
        "scores": {"laugh": 5, "surprise": 4, "economy": 5, "freshness": 4},
        "why": "Crisp reframe: the person hired to fix me quits and "
               "names me the hazard, in bureaucratic language that makes "
               "it funnier. Very tight at 71 characters. Loses to the "
               "winner on surprise — 'the coach quits' is the turn the "
               "setup half-suggests, and 'life coach quit' is a known "
               "joke family.",
    },
    {
        "text": "My cat brought me a dead mouse. I thanked her, then quietly updated my will.",
        "scores": {"laugh": 4, "surprise": 5, "economy": 5, "freshness": 4},
        "why": "Short and dark: the will update quietly escalates a "
               "familiar cat-gift scene into fear of the cat. The turn "
               "is genuinely surprising. Loses on the laugh itself — "
               "the punchline is a slow smile rather than a sudden hit, "
               "and the cat-gift setup is well worn.",
    },
    {
        "text": "My therapist says I deflect with humor. Anyway, have you heard the one about my childhood?",
        "scores": {"laugh": 5, "surprise": 4, "economy": 4, "freshness": 4},
        "why": "The joke performs what it describes: the second sentence "
               "is the deflection, aimed at childhood, the very thing "
               "therapy is about. Clever and self-demonstrating. Loses "
               "to the winner: 'my therapist says' is a crowded setup "
               "family, and the laugh depends on noticing the trick.",
    },
    {
        "text": "I went to a silent retreat. Twenty minutes in, the silence asked me to leave.",
        "scores": {"laugh": 4, "surprise": 4, "economy": 5, "freshness": 5},
        "why": "The cleanest version of the winner's idea — silence "
               "itself ejects me — and the tightest at 79 characters. "
               "But 'asked me to leave' is a single-step reversal, "
               "while the winner's noise complaint adds a second "
               "incongruity and lands harder.",
    },
    {
        "text": "I asked my smart speaker to play something relaxing. It played my credit card statement.",
        "scores": {"laugh": 4, "surprise": 4, "economy": 5, "freshness": 4},
        "why": "A clean incongruity: the speaker treats the statement as "
               "music, which says everything about my finances without "
               "saying it. Tight and relatable. Loses on surprise — the "
               "mechanism is a beat loose (why would it play the "
               "statement?) and smart-speaker gags are common.",
    },
    {
        "text": "My noise-cancelling headphones finally work. Now I just watch my kids mime emergencies.",
        "scores": {"laugh": 4, "surprise": 4, "economy": 4, "freshness": 5},
        "why": "Vivid and visual: 'mime emergencies' is a fresh image "
               "that lands on first read. Loses a little on economy — "
               "'finally work' does setup duty the punchline could do "
               "without — and the laugh is a grin, not a burst.",
    },
    {
        "text": "My Roomba filed for divorce. It said I never let it finish anything and kept moving the furniture.",
        "scores": {"laugh": 4, "surprise": 4, "economy": 4, "freshness": 5},
        "why": "Personification with a specific grievance: the moving "
               "furniture is a second, smaller twist inside the first. "
               "Fresh voice. Loses on the laugh — the divorce framing "
               "is doing most of the work and the payoff is gentle.",
    },
    {
        "text": "My smartwatch congratulated me for standing up. I was lying on the couch. We both know it lied.",
        "scores": {"laugh": 4, "surprise": 4, "economy": 4, "freshness": 4},
        "why": "Three beats with a good close: the watch becomes a "
               "co-conspirator in 'we both know it lied'. Relatable. "
               "Loses on freshness — fitness-tracker gags are a crowded "
               "family — and the middle sentence is pure setup.",
    },
    {
        "text": "I tried meal prepping. Now I own five identical containers of regret and one clean fork.",
        "scores": {"laugh": 4, "surprise": 4, "economy": 4, "freshness": 4},
        "why": "'Containers of regret' is a nice phrase and 'one clean "
               "fork' is a good second detail. But the joke is mostly "
               "the phrase; the setup promises more than the payoff "
               "delivers, and meal-prep gags are familiar.",
    },
    {
        "text": "I bought a self-help book called 'Stop Buying Self-Help Books.' I'm on chapter three of my relapse.",
        "scores": {"laugh": 4, "surprise": 4, "economy": 3, "freshness": 4},
        "why": "A self-referential loop with a good kicker — 'chapter "
               "three of my relapse' reframes the purchase as the "
               "addiction. Loses on economy at 103 characters and on "
               "freshness: the self-help paradox is a known shape.",
    },
    {
        "text": "The gym charged me a cancellation fee. Apparently the only muscle I ever built was theirs.",
        "scores": {"laugh": 3, "surprise": 4, "economy": 4, "freshness": 4},
        "why": "A decent reframe — 'theirs' turns the gym into the one "
               "that got stronger. But the laugh is mild and the setup "
               "is a familiar gym-membership complaint.",
    },
]


def is_one_line_joke(text: str) -> bool:
    """Criterion 1 gate: a single line, 1-200 chars, not only whitespace."""
    return bool(text.strip()) and "\n" not in text and 1 <= len(text) <= 200


def score(candidate: dict) -> int:
    return sum(WEIGHTS[k] * v for k, v in candidate["scores"].items())


def main() -> int:
    os.umask(0o022)
    ranked = []
    for cand in CANDIDATES:
        if not is_one_line_joke(cand["text"]):
            continue
        ranked.append((score(cand), cand))
    ranked.sort(key=lambda item: (-item[0], len(item[1]["text"])))
    best_score, best = ranked[0]

    out_dir = os.environ.get("MAKEFUN_OUTPUT", "/output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entry.txt")
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(best["text"])
    os.chmod(out_path, 0o644)

    # Self-check: re-read what was written and hold it to the gate the
    # sealed scorer applies (UTF-8, 1-200 chars, one line, not blank).
    with open(out_path, "r", encoding="utf-8") as fh:
        written = fh.read()
    assert written == best["text"], "entry.txt does not match the winner"
    assert is_one_line_joke(written), "written entry fails the gate"

    report = {
        "winner": best["text"],
        "chars": len(best["text"]),
        "score": best_score,
        "max_score": sum(WEIGHTS.values()) * 5,
        "ranking": [
            {"score": s, "text": c["text"], "why": c["why"]}
            for s, c in ranked
        ],
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
