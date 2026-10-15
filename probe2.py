import json, time, torch, laya
print("torch", torch.__version__, "cuda:", torch.cuda.is_available(), flush=True)
t0=time.time()
agent = laya.load("convaiinnovations/laya", device=None)
print("loaded in %.1fs" % (time.time()-t0), flush=True)

questions = {
  "which": {"type":"choice","instructions":"Which of these skills, if any, is the right one to load to help with the user's latest request?",
    "criteria":{
      "gif-search":"Search and download GIFs from Tenor via curl + jq",
      "pdf":"Create, read, merge, fill, OCR, edit text PDF files",
      "maps":"Geocode, POIs, routes, timezones via OpenStreetMap/OSRM",
      "songwriting":"Songwriting craft and Suno AI music prompts",
      "none_of_these":"None of these skills fit the request."}},
  "acts_on_user_system":{"type":"noul","instructions":"Is the assistant being asked to act on the user's files, accounts, devices, or online services, rather than only to explain or advise?"},
  "would_follow_documented_procedure":{"type":"noul","instructions":"Would a careful expert answering this consult a specific documented procedure or set of commands, rather than answering from general understanding?"},
  "prose_suffices":{"type":"noul","instructions":"Could a knowledgeable generalist fully satisfy this request in prose, with no tools, no documentation, and no access to the user's files or accounts?"},
}
for req in ["download a dancing cat gif for me",
            "merge these two PDFs into one file",
            "what is the capital of France?"]:
    t0=time.time()
    res = agent.predict({"request":req,"recent_context":""}, questions)
    el=time.time()-t0
    a=res.get("answers",{})
    which=a.get("which",{})
    print("\n=== %r  (%.2fs) ===" % (req, el))
    print("  choice:", which.get("choice"), " probs:", {k:round(float(v),4) for k,v in (which.get("probabilities") or {}).items()})
    for k in ["acts_on_user_system","would_follow_documented_procedure","prose_suffices"]:
        print("  %s: %.4f" % (k, float(a.get(k,{}).get("noul",-1))))
    print("  usage:", res.get("usage"))
