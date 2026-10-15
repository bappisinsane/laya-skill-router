"""Laya decision server for the Hermes laya-skill-router plugin.

Wraps ``laya.serve`` (which already speaks TypeSafe's /v1/systemone wire protocol) and
raises one safety constant before the app is built.

Why the cap has to move: ``laya.serve.MAX_CHOICE_OPTIONS`` is 100, but a Hermes roster is
routinely larger than that (123 skills on this machine). The limit is a server-side guard,
not a model limit -- measured directly, one choice over the whole 123-skill roster picks
correctly and sharply (gif-search 0.997, pdf 1.0, powerpoint 0.664), whereas the chunking
that the cap forces is what degrades the decision head. Raising the guard therefore makes
the router both simpler (one forward pass, no chunks, no cross-chunk probability merge) and
more accurate. The model's own input budget is enforced separately via ``max_len``.

Configuration is entirely via environment variables (same names laya.serve uses):
  LAYA_HOST, LAYA_PORT, LAYA_DEVICE, LAYA_MODELS, LAYA_PRELOAD, LAYA_MAX_LOADED,
  LAYA_DEFAULT_MODEL, LAYA_API_KEY, LAYA_LOG_LEVEL, LAYA_THREADS
"""

from __future__ import annotations

import os

import laya.serve as _serve

#: 250 keeps a wide margin over any realistic roster while staying far below the
#: per-question token budget the head can actually read.
ROSTER_CHOICE_CAP = int(os.environ.get("LAYA_ROSTER_CAP", "250"))

if _serve.MAX_CHOICE_OPTIONS < ROSTER_CHOICE_CAP:
    _serve.MAX_CHOICE_OPTIONS = ROSTER_CHOICE_CAP


def main() -> None:
    _serve.main()


if __name__ == "__main__":
    main()
