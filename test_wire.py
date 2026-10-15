"""Validate the local Laya server against the Jev /v1/systemone wire protocol.

Sends exactly the payload shape the existing typesafe-skill-router plugin builds
(state dict + choice criteria + noul questions) and checks the answer shape the
plugin's client parses: answers[<qid>].choice / .probabilities / .noul, plus usage.
"""
import json
import time
import urllib.request

URL = "http://127.0.0.1:8100/v1/systemone"

SKILLS = {
    "gif-search": "Search/download GIFs from Tenor via curl + jq",
    "pdf": "PDF files: create, read, merge, fill, OCR, edit text",
    "maps": "Geocode, POIs, routes, timezones via OpenStreetMap/OSRM",
    "xlsx": "Create, read, edit Excel .xlsx workbooks and CSVs",
    "arxiv": "Search arXiv papers by keyword, author, category, or ID",
    "github": "GitHub via gh CLI: PRs, issues, reviews, repos, auth",
    "himalaya": "Himalaya CLI: IMAP/SMTP email from terminal",
    "powerpoint": "Create, read, edit .pptx decks with python-pptx",
}

payload = {
    "state": {"request": "merge these two PDFs into one file", "recent_context": ""},
    "model": "english",
    "questions": {
        "which": {
            "type": "choice",
            "instructions": "Which of these skills, if any, is the right one to load "
                            "to help with the user's latest request?",
            "criteria": SKILLS,
        },
        "acts_on_user_system": {
            "type": "noul",
            "instructions": "Is the assistant being asked to act on the user's files, accounts, "
                            "devices, or online services, rather than only to explain or advise?",
        },
        "would_follow_documented_procedure": {
            "type": "noul",
            "instructions": "Would a careful expert answering this consult a specific documented "
                            "procedure or set of commands, rather than answering from general understanding?",
        },
        "prose_suffices": {
            "type": "noul",
            "instructions": "Could a knowledgeable generalist fully satisfy this request in prose, "
                            "with no tools, no documentation, and no access to the user's files or accounts?",
        },
    },
}

body = json.dumps(payload).encode()
req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"}, method="POST")
t0 = time.time()
with urllib.request.urlopen(req, timeout=120) as h:
    raw = json.loads(h.read().decode())
el = time.time() - t0

print("latency: %.2fs" % el)
print(json.dumps(raw, indent=2)[:2500])

# Now assert the exact fields the plugin's client.py reads
ans = raw.get("answers") or {}
w = ans.get("which") or {}
print("\n--- plugin-compat checks ---")
print("model            :", raw.get("model"))
print("answers['which']['choice']        :", w.get("choice"))
print("answers['which']['probabilities'] :", {k: round(float(v), 4) for k, v in (w.get("probabilities") or {}).items()})
print("answers['which']['confidence']    :", w.get("confidence"))
for k in ("acts_on_user_system", "would_follow_documented_procedure", "prose_suffices"):
    print("answers[%r]['noul']  : %s" % (k, (ans.get(k) or {}).get("noul")))
print("usage            :", raw.get("usage"))
print("has 'type' per answer:", {k: v.get("type") for k, v in ans.items()})
