import laya, json, inspect
from laya.agent import build_sequence
agent = laya.load("convaiinnovations/laya", device=None)
tok = agent.tokenizer if hasattr(agent,'tokenizer') else None
print("agent attrs:", [a for a in dir(agent) if not a.startswith('_')][:40])

SK = {"gif-search":"Search/download GIFs from Tenor via curl + jq",
      "pdf":"PDF files: create, read, merge, fill, OCR, edit text",
      "maps":"Geocode, POIs, routes, timezones via OpenStreetMap/OSRM"}
INSTR = "Which of these skills, if any, is the right one to load to help with the user's latest request?"

# 1) does a 3-option choice discriminate?
q = {"which":{"type":"choice","instructions":INSTR,"criteria":dict(SK)}}
for req in ["download a dancing cat gif for me","merge these two PDFs into one file","how far is Sylhet from Dhaka by road?"]:
    r = agent.predict({"request":req}, q)
    a=r["answers"]["which"]
    print("3opt %-40s -> %-12s %s" % (req[:40], a.get("choice"), {k:round(float(v),3) for k,v in (a.get("probabilities") or {}).items()}))

print()
# 2) option token budget stats
if tok is not None:
    q1 = {"type":"choice","instructions":INSTR,"criteria":dict(SK)}
    out = build_sequence(tok, {"request":"x"}, q1, return_stats=True, return_truncation_stats=True)
    print("build_sequence returns", len(out), "values")
    for i,o in enumerate(out):
        print("  [%d]"%i, str(o)[:300])
