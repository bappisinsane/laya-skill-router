import json, time, laya
agent = laya.load("convaiinnovations/laya", device=None)

SKILLS = {
 "gif-search":"Search/download GIFs from Tenor via curl + jq",
 "pdf":"PDF files: create, read, merge, fill, OCR, edit text",
 "maps":"Geocode, POIs, routes, timezones via OpenStreetMap/OSRM",
 "songwriting-and-ai-music":"Songwriting craft and Suno AI music prompts",
 "xlsx":"Create, read, edit Excel .xlsx workbooks and CSVs",
 "docx":"Create, read, edit, template, and review Word .docx files",
 "arxiv":"Search arXiv papers by keyword, author, category, or ID",
 "github":"GitHub via gh CLI: PRs, issues, reviews, repos, auth",
 "himalaya":"Himalaya CLI: IMAP/SMTP email from terminal",
 "obsidian":"Read, search, create, and edit notes in the Obsidian vault",
}
CASES = [
 ("download a dancing cat gif for me","gif-search"),
 ("merge these two PDFs into one file","pdf"),
 ("how far is Sylhet from Dhaka by road?","maps"),
 ("make me a spreadsheet of monthly expenses","xlsx"),
 ("find recent papers on RLHF calibration","arxiv"),
 ("open a pull request for my branch","github"),
 ("what is the capital of France?",None),
 ("tell me a joke",None),
 ("explain how transformers work",None),
]

def run(label, instr, nonew, state_mode, use_none=True):
    crit = dict(SKILLS)
    if use_none: crit["none_of_these"] = nonew
    q = {"which":{"type":"choice","instructions":instr,"criteria":crit}}
    ok=0; n=0
    rows=[]
    for req, expect in CASES:
        state = {"request":req} if state_mode=="dict" else req
        r = agent.predict(state, q)
        a = r["answers"]["which"]
        got = a.get("choice")
        p = {k:round(float(v),4) for k,v in (a.get("probabilities") or {}).items()}
        top = sorted(p.items(), key=lambda kv:-kv[1])[:2]
        n+=1
        if expect is None:
            good = (got=="none_of_these")
        else:
            good = (got==expect)
        ok += good
        rows.append((req[:42], expect, got, top, good))
    print("\n#### %s  -> %d/%d" % (label, ok, n))
    for r in rows:
        print("   %-44s exp=%-22s got=%-22s %s  top=%s" % (r[0], r[1], r[2], "OK " if r[4] else "XX ", r[3]))

INSTR = "Which of these skills, if any, is the right one to load to help with the user's latest request?"
run("A dict-state, Jev instr, none='None of these skills fit the request.'", INSTR, "None of these skills fit the request.", "dict")
run("B str-state,  Jev instr, same none", INSTR, "None of these skills fit the request.", "str")
run("C str-state, backtick instr, same none", "Which of these skills, if any, is the right one to load to help with `request`?", "None of these skills fit the request.", "str")
run("D str-state, no none option at all", INSTR, "", "str", use_none=False)
