import json, time, laya
print("device probe...")
import torch
print("torch", torch.__version__, "cuda avail:", torch.cuda.is_available())

t0=time.time()
agent = laya.load("convaiinnovations/laya", device=None)
print("loaded in %.1fs" % (time.time()-t0))

questions = {
  "which": {"type":"choice","instructions":"Which of these skills, if any, is the right one to load to help with the user's latest request?",
    "criteria":{
      "gif-search":"Search and download GIFs from Tenor",
      "pdf":"Create, read, merge, fill, OCR PDF files",
      "maps":"Geocode, POIs, routes, timezones via OpenStreetMap",
      "none_of_these":"None of these skills fit the request."}},
  "acts_on_user_system":{"type":"noul","instructions":"Is the assistant being asked to act on the user's files, accounts, devices, or online services, rather than only to explain or advise?"},
  "prose_suffices":{"type":"noul","instructions":"Could a knowledgeable generalist fully satisfy this request in prose, with no tools, no documentation, and no access to the user's files or accounts?"},
}
state = {"request":"download a dancing cat gif for me","recent_context":""}
t0=time.time()
res = agent.predict(state, questions)
print("predict in %.2fs" % (time.time()-t0))
print(json.dumps(res, indent=2, default=str)[:3000])
