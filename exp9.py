"""Two-pronged attack on the remaining failures.

1. Router: auto-routes between all three checkpoints (english/multilingual/typed-decisions).
2. head_max_len tuning: give the choice head more budget to read option descriptions.

Remaining failures at typed-decisions + max_len=512:
  - "how far is Sylhet from Dhaka by road?" → maps (got inspecting-hermes-desktop-dom)
  - "read my email inbox" → himalaya (got email-inbox-triage @ 0.984)
"""
import json
import os
import re
import time
from pathlib import Path

import laya
from laya import Router

HOME = Path(os.environ.get("HERMES_HOME") or (Path.home() / ".hermes"))
ROOT = HOME / "skills"
FM = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse(p):
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
    return {"name": name, "description": desc}


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


SKILLS = roster()
print("ROSTER: %d" % len(SKILLS), flush=True)

CHOICE_INSTR = ("Which of these skills, if any, is the right one to load to help with "
                "the user's latest request?")
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

crit = {s["name"]: s["description"] for s in SKILLS}
q = {"which": {"type": "choice", "instructions": CHOICE_INSTR, "criteria": crit}}

# ── Approach 1: Router (auto-routes between all 3 checkpoints) ──
print("\n" + "=" * 70)
print("APPROACH 1: Router (auto-route)")
print("=" * 70, flush=True)
router = Router(preload=True, device=None)
ok = 0
for req, exp in CASES:
    try:
        t0 = time.time()
        r = router.predict({"request": req}, q, max_len=512)
        el = time.time() - t0
        a = r["answers"]["which"]
        got = a.get("choice")
        probs = {k: float(v) for k, v in (a.get("probabilities") or {}).items()}
        top = sorted(probs.items(), key=lambda kv: (-kv[1], kv[0]))[:3]
        good = (got == exp) if exp else True
        ok += good
        routed = r.get("routing", {}).get("model", "?")
        print("  %-42s exp=%-12s got=%-24s %s routed=%-14s top=%s (%.1fs)"
              % (req[:42], exp or "NONE", str(got)[:24], "OK " if good else "XX ",
                 routed, [(n[:16], round(p, 3)) for n, p in top], el), flush=True)
    except Exception as e:
        print("  %-42s ERROR %s: %s" % (req[:42], type(e).__name__, str(e)[:120]), flush=True)
print("  --> %d/%d" % (ok, len(CASES)), flush=True)

# ── Approach 2: typed-decisions with larger head_max_len ──
print("\n" + "=" * 70)
print("APPROACH 2: typed-decisions + head_max_len=384")
print("=" * 70, flush=True)
agent = laya.load("convaiinnovations/laya", subfolder="typed-decisions", device=None)
agent.cfg["head_max_len"] = 384
agent.cfg["max_len"] = 1024
ok = 0
for req, exp in CASES:
    try:
        t0 = time.time()
        r = agent.predict({"request": req}, q)
        el = time.time() - t0
        a = r["answers"]["which"]
        got = a.get("choice")
        probs = {k: float(v) for k, v in (a.get("probabilities") or {}).items()}
        top = sorted(probs.items(), key=lambda kv: (-kv[1], kv[0]))[:3]
        good = (got == exp) if exp else True
        ok += good
        print("  %-42s exp=%-12s got=%-24s %s top=%s (%.1fs)"
              % (req[:42], exp or "NONE", str(got)[:24], "OK " if good else "XX ",
                 [(n[:16], round(p, 3)) for n, p in top], el), flush=True)
    except Exception as e:
        print("  %-42s ERROR %s: %s" % (req[:42], type(e).__name__, str(e)[:120]), flush=True)
print("  --> %d/%d" % (ok, len(CASES)), flush=True)

# ── Approach 3: typed-decisions with head_max_len=512 ──
print("\n" + "=" * 70)
print("APPROACH 3: typed-decisions + head_max_len=512")
print("=" * 70, flush=True)
agent2 = laya.load("convaiinnovations/laya", subfolder="typed-decisions", device=None)
agent2.cfg["head_max_len"] = 512
agent2.cfg["max_len"] = 1024
ok = 0
for req, exp in CASES:
    try:
        t0 = time.time()
        r = agent2.predict({"request": req}, q)
        el = time.time() - t0
        a = r["answers"]["which"]
        got = a.get("choice")
        probs = {k: float(v) for k, v in (a.get("probabilities") or {}).items()}
        top = sorted(probs.items(), key=lambda kv: (-kv[1], kv[0]))[:3]
        good = (got == exp) if exp else True
        ok += good
        print("  %-42s exp=%-12s got=%-24s %s top=%s (%.1fs)"
              % (req[:42], exp or "NONE", str(got)[:24], "OK " if good else "XX ",
                 [(n[:16], round(p, 3)) for n, p in top], el), flush=True)
    except Exception as e:
        print("  %-42s ERROR %s: %s" % (req[:42], type(e).__name__, str(e)[:120]), flush=True)
print("  --> %d/%d" % (ok, len(CASES)), flush=True)
