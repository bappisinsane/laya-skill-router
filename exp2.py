import json, laya, inspect
print("DEFAULT_MODELS:", laya.DEFAULT_MODELS)
print()
print("QTYPES:", laya.QTYPES, "QTYPE_NAMES:", laya.QTYPE_NAMES)
print()
# how is state rendered into the sequence?
import laya.agent as A
for name in ["build_sequence","_render_state","render_state","format_state"]:
    f=getattr(A,name,None)
    if f: print("FOUND", name); print(inspect.getsource(f)[:1500]); print("---")
