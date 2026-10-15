import laya, json
agent = laya.load("convaiinnovations/laya", device=None)
INSTR = "Which of these skills, if any, is the right one to load to help with the user's latest request?"

POOL = [
 ("gif-search","Search/download GIFs from Tenor via curl + jq"),
 ("pdf","PDF files: create, read, merge, fill, OCR, edit text"),
 ("maps","Geocode, POIs, routes, timezones via OpenStreetMap/OSRM"),
 ("xlsx","Create, read, edit Excel .xlsx workbooks and CSVs"),
 ("docx","Create, read, edit, template, and review Word .docx files"),
 ("arxiv","Search arXiv papers by keyword, author, category, or ID"),
 ("github","GitHub via gh CLI: PRs, issues, reviews, repos, auth"),
 ("himalaya","Himalaya CLI: IMAP/SMTP email from terminal"),
 ("obsidian","Read, search, create, and edit notes in the Obsidian vault"),
 ("powerpoint","Create, read, edit .pptx decks with python-pptx"),
 ("notion","Notion API + ntn CLI: pages, databases, markdown, Workers"),
 ("airtable","Airtable REST API via curl. Records CRUD, filters, upserts"),
 ("songsee","Audio spectrograms/features (mel, chroma, MFCC) via CLI"),
 ("manim-video","Manim CE animations: 3Blue1Brown math/algo videos"),
 ("p5js","p5.js sketches: gen art, shaders, interactive, 3D"),
 ("spotify","Control Spotify playback"),
 ("weather","Get weather forecasts"),
 ("calendar","Manage calendar events"),
 ("slack","Send Slack messages"),
 ("docker","Build and run containers"),
]
CASES = [("download a dancing cat gif for me","gif-search"),
         ("merge these two PDFs into one file","pdf"),
         ("how far is Sylhet from Dhaka by road?","maps")]

print("%-8s %-6s  %s" % ("n_opts","acc","detail"))
for n in [3,5,8,10,12,16,20]:
    sub = POOL[:n]
    # ensure the expected skill is in the subset
    names = {s[0] for s in sub}
    if not all(e in names for _,e in CASES): continue
    q = {"which":{"type":"choice","instructions":INSTR,"criteria":dict(sub)}}
    ok=0; det=[]
    for req,exp in CASES:
        r=agent.predict({"request":req}, q)
        a=r["answers"]["which"]; got=a.get("choice")
        p=a.get("probabilities") or {}
        ok += (got==exp)
        det.append("%s->%s(%.2f)" % (exp[:5], (got or "?")[:8], float(p.get(exp,0))))
    print("%-8d %-6s  %s" % (n, "%d/3"%ok, "  ".join(det)))
