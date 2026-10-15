"""Chunked-choice design test: mirror the Jev two-stage recipe onto Laya's limits.

Laya caps a single choice at 100 options and its choice head degrades well before that,
but it answers many questions in ONE forward pass. So stage 1 asks one choice per chunk
of the roster (no none_of_these: Laya's none option is degenerate at P~1.0), then the
best chunk's argmax goes to stage 2 with full descriptions plus per-candidate fits nouls.
"""
import json
import os
import re
import time
from pathlib import Path

import laya

HOME = Path(os.environ.get("HERMES_HOME") or (Path.home() / ".hermes"))
ROOT = HOME / "skills"
FM = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse(p: Path) -> dict:
    t = p.read_text(encoding="utf-8", errors="replace")
    m = FM.match(t)
    meta, body = {}, t
    if m:
        body = t[m.end():]
        for line in m.group(1).splitlines():
            if ":" in line and not line.startswith((" ", "\t")):
                k, _, v = line.partition(":")
                if k.strip() in ("name", "description"):
                    meta[k.strip()] = v.strip().strip('"').strip("'")
    name = (meta.get("name") or p.parent.name).strip()
    desc = " ".join((meta.get("description") or "").split())
    if not desc:
        for l in body.splitlines():
            if l.strip() and not l.startswith("#"):
                desc = l.strip()
                break
    return {"name": name, "description": desc, "excerpt": " ".join(body[:700].split())}


def roster():
    out, seen = [], set()
    for p in sorted(ROOT.rglob("SKILL.md")):
        if any(part.startswith(".") for part in p.relative_to(ROOT).parts):
            continue
        s = parse(p)
        if s["name"] in seen:
            continue
        seen.add(s["name"])
        out.append(s)
    return out


def chunks(items, size):
    return [items[i:i + size] for i in range(0, len(items), size)]


SKILLS = roster()
BY_NAME = {s["name"]: s for s in SKILLS}
print("ROSTER: %d skills" % len(SKILLS), flush=True)

agent = laya.load("convaiinnovations/laya", device=None)

CHOICE_INSTR = ("Which of these skills, if any, is the right one to load to help with "
                "the user's latest request?")
FITS_INSTR = ("Does the skill '%s' do the specific thing the user's request asks for? "
              "It is described as: %s")

CASES = [
    ("download a dancing cat gif for me", "gif-search"),
    ("merge these two PDFs into one file", "pdf"),
    ("how far is Sylhet from Dhaka by road?", "maps"),
    ("make me a spreadsheet of monthly expenses", "xlsx"),
    ("find recent papers on RLHF calibration", "arxiv"),
    ("open a pull request for my branch", "github"),
    ("read my email inbox", "himalaya"),
    ("create a slide deck about Q3 results", "powerpoint"),
    ("what is the capital of France?", None),
    ("tell me a joke", None),
    ("explain how transformers work", None),
]


def stage1(request, chunk_size):
    groups = chunks(SKILLS, chunk_size)
    questions = {}
    for i, g in enumerate(groups):
        questions["chunk%d" % i] = {
            "type": "choice",
            "instructions": CHOICE_INSTR,
            "criteria": {s["name"]: s["description"] for s in g},
        }
    t0 = time.time()
    r = agent.predict({"request": request, "recent_context": ""}, questions)
    el = time.time() - t0
    best, best_p, best_chunk = None, -1.0, -1
    per = []
    for i in range(len(groups)):
        a = r["answers"]["chunk%d" % i]
        probs = {k: float(v) for k, v in (a.get("probabilities") or {}).items()}
        top = sorted(probs.items(), key=lambda kv: (-kv[1], kv[0]))[:3]
        per.append(top)
        if top and top[0][1] > best_p:
            best, best_p, best_chunk = top[0][0], top[0][1], i
    return {"best": best, "p": best_p, "chunk": best_chunk, "per": per, "secs": el,
            "usage": r.get("usage")}


def stage2(request, names):
    crit = {}
    for n in names:
        s = BY_NAME[n]
        crit[n] = "%s\n\nSKILL.md: %s" % (s["description"], s["excerpt"]) if s["excerpt"] else s["description"]
    crit["none_of_these"] = "None of these skills fit the request."
    questions = {"which": {"type": "choice", "instructions":
                           "Exactly one of these skills is the right one to load for the "
                           "user's latest request. Which one? Read what each actually does, "
                           "not just its name.", "criteria": crit}}
    for n in names:
        questions["fits::" + n] = {"type": "noul", "instructions": FITS_INSTR % (n, BY_NAME[n]["description"])}
    t0 = time.time()
    r = agent.predict({"request": request, "recent_context": ""}, questions)
    el = time.time() - t0
    picked = r["answers"]["which"].get("choice")
    fits = {k.removeprefix("fits::"): float(v.get("noul", 0.0))
            for k, v in r["answers"].items() if k.startswith("fits::")}
    return {"picked": picked, "fits": fits, "secs": el, "usage": r.get("usage")}


for chunk_size in (10, 20):
    print("\n########## chunk_size=%d ##########" % chunk_size, flush=True)
    ok = 0
    for req, exp in CASES:
        s1 = stage1(req, chunk_size)
        names = [n for n, _ in s1["per"][s1["chunk"]][:3]]
        s2 = stage2(req, names)
        got = s2["picked"]
        winner_fits = s2["fits"].get(got, 0.0)
        good = (got == exp) if exp else (got in (None, "none_of_these"))
        ok += good
        print("  %-42s exp=%-12s s1=%-26s s2=%-26s fits=%.2f %s (s1 %.1fs s2 %.1fs)"
              % (req[:42], exp or "NONE", str(s1["best"])[:26], str(got)[:26], winner_fits,
                 "OK " if good else "XX ", s1["secs"], s2["secs"]), flush=True)
    print("  --> %d/%d" % (ok, len(CASES)), flush=True)
