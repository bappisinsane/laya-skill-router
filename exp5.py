import laya, os, re, json, time
from pathlib import Path

# --- build the real roster (same logic as the Jev plugin's roster.py) ---
HOME = Path(os.environ.get("HERMES_HOME") or (Path.home()/".hermes"))
ROOT = HOME/"skills"
FM = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
def parse(p):
    t=p.read_text(encoding="utf-8",errors="replace")
    m=FM.match(t); meta={}; body=t
    if m:
        body=t[m.end():]
        for line in m.group(1).splitlines():
            if ":" in line and not line.startswith((" ","\t")):
                k,_,v=line.partition(":")
                if k.strip() in ("name","description"): meta[k.strip()]=v.strip().strip('"').strip("'")
    name=(meta.get("name") or p.parent.name).strip()
    desc=" ".join((meta.get("description") or "").split())
    if not desc:
        for l in body.splitlines():
            if l.strip() and not l.startswith("#"): desc=l.strip(); break
    return {"name":name,"description":desc,"excerpt":" ".join(body[:700].split())}
skills=[]
seen=set()
for p in sorted(ROOT.rglob("SKILL.md")):
    if any(part.startswith(".") for part in p.relative_to(ROOT).parts): continue
    s=parse(p)
    if s["name"] in seen: continue
    seen.add(s["name"]); skills.append(s)
print("ROSTER:", len(skills), "skills")

agent = laya.load("convaiinnovations/laya", device=None)
embed = laya.embed_fn_from_agent(agent)

INSTR = "Which of these skills, if any, is the right one to load to help with the user's latest request?"
crit = {s["name"]: s["description"] for s in skills}

CASES = [("download a dancing cat gif for me","gif-search"),
         ("merge these two PDFs into one file","pdf"),
         ("how far is Sylhet from Dhaka by road?","maps"),
         ("make me a spreadsheet of monthly expenses","xlsx"),
         ("find recent papers on RLHF calibration","arxiv"),
         ("open a pull request for my branch","github"),
         ("read my email inbox","himalaya"),
         ("create a slide deck about Q3 results","powerpoint"),
         ("what is the capital of France?",None),
         ("tell me a joke",None),
         ("explain how transformers work",None)]

q = {"which":{"type":"choice","instructions":INSTR,"criteria":crit},
     "acts_on_user_system":{"type":"noul","instructions":"Is the assistant being asked to act on the user's files, accounts, devices, or online services, rather than only to explain or advise?"},
     "prose_suffices":{"type":"noul","instructions":"Could a knowledgeable generalist fully satisfy this request in prose, with no tools, no documentation, and no access to the user's files or accounts?"}}

for k in [5,8,12,20]:
    print("\n===== k=%d =====" % k)
    ok=0
    for req,exp in CASES:
        t0=time.time()
        r = laya.predict_shortlist(agent, {"request":req}, q, embed, k=k)
        el=time.time()-t0
        got = r["answers"]["which"].get("choice")
        sl = r.get("shortlist",{}).get("which",{})
        labels = sl.get("labels",[])
        good = (got==exp) if exp else (got=="none_of_these" or got is None)
        ok+=good
        print("  %-42s exp=%-12s got=%-22s %s k_used=%s (%.2fs)" % (req[:42], exp or "NONE", str(got)[:22], "OK " if good else "XX ", len(labels), el))
    print("  --> %d/%d" % (ok, len(CASES)))
