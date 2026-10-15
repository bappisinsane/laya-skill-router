# Laya Skill Router

> **Non-autoregressive skill routing for Hermes Agent.** A single forward pass, ~35 ms, picks the right skill from your roster — no LLM call, no token cost, no hallucination.

---

## What It Is

Laya Skill Router is a lightweight HTTP server that wraps [Laya](https://github.com/NandhaKishorM/laya) — a multilingual, non-autoregressive System 1 decision model — and exposes it as a **skill router** for [Hermes Agent](https://hermes-agent.nousresearch.com).

Instead of asking an LLM "which skill should I load?", the router uses a fine-tuned ModernBERT-large (421M params) that answers typed questions in a single forward pass. It evaluates your full skill roster as choice criteria and returns calibrated probabilities for each option.

**Key properties:**

| Property | Value |
|---|---|
| **Latency** | ~35 ms (GPU) / ~200 ms (CPU) per request |
| **Token cost** | 0 (non-autoregressive — no generation) |
| **Model size** | 421M params (ModernBERT-large backbone) |
| **Languages** | 100+ (auto-routes English vs. multilingual) |
| **Calibration** | Temperature-fitted, ECE 0.081 |
| **Roster size** | Up to 250 skills (configurable) |

---

## How It Works

```
User request
    │
    ▼
┌─────────────────────────────┐
│  POST /v1/systemone         │
│                             │
│  state: { request, context }│
│  questions:                 │
│    which → choice (roster)  │
│    acts_on_user_system      │
│    would_follow_procedure   │
│    prose_suffices           │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  Laya Decision Model        │
│  (single forward pass)      │
│                             │
│  1. Detect language         │
│  2. Route to checkpoint     │
│  3. Score all skills        │
│  4. Answer guardrails       │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  Response                   │
│                             │
│  which: pdf (96.2%)         │
│  acts_on_user_system: no    │
│  prose_suffices: no         │
│  usage: { tokens, time }    │
└─────────────────────────────┘
```

The router asks four questions in one pass:

1. **`which`** (choice) — "Which skill is the right one?" — scores every skill in your roster
2. **`acts_on_user_system`** (noul) — "Does this touch files, accounts, or devices?"
3. **`would_follow_documented_procedure`** (noul) — "Would an expert consult documentation?"
4. **`prose_suffices`** (noul) — "Could a generalist answer in plain text?"

The guardrails let Hermes decide whether to load a skill at all, or just answer directly.

---

## Quick Start

### Prerequisites

- Python 3.10+
- [Hermes Agent](https://hermes-agent.nousresearch.com) (for the plugin integration)
- ~2 GB disk for model checkpoints (downloaded on first use)

### Install

```bash
git clone https://github.com/bappisinsane/laya-skill-router.git
cd laya-skill-router
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install "laya[serve]"
```

### Run

```bash
# Start the server (preloads all checkpoints)
LAYA_PORT=8100 LAYA_PRELOAD=1 laya-serve

# Or use the bundled wrapper (raises roster cap to 250)
LAYA_PORT=8100 .venv/Scripts/python.exe serve_laya.py
```

### Test

```bash
curl -s http://127.0.0.1:8100/v1/systemone \
  -H 'Content-Type: application/json' \
  -d '{
    "state": {"request": "merge these two PDFs into one file"},
    "questions": {
      "which": {
        "type": "choice",
        "instructions": "Which skill should handle this?",
        "criteria": {
          "pdf": "Create, read, merge, fill, OCR PDF files",
          "gif-search": "Search and download GIFs",
          "maps": "Geocode, POIs, routes"
        }
      },
      "acts_on_user_system": {
        "type": "noul",
        "instructions": "Does this touch the user's files or accounts?"
      }
    }
  }'
```

---

## Configuration

All configuration is via environment variables:

| Variable | Default | Description |
|---|---|---|
| `LAYA_HOST` | `127.0.0.1` | Bind address |
| `LAYA_PORT` | `8100` | Bind port |
| `LAYA_DEVICE` | `cpu` | `cpu` or `cuda` |
| `LAYA_MODELS` | `english` | Comma-separated checkpoint list |
| `LAYA_PRELOAD` | `1` | Preload checkpoints at startup |
| `LAYA_MAX_LOADED` | `1` | Max checkpoints to keep in memory |
| `LAYA_ROSTER_CAP` | `250` | Max skills in a single choice question |
| `LAYA_API_KEY` | — | Bearer token for auth (optional) |

---

## API

### `POST /v1/systemone`

**Request:**

```json
{
  "state": {
    "request": "download a dancing cat gif",
    "recent_context": ""
  },
  "model": "english",
  "questions": {
    "which": {
      "type": "choice",
      "instructions": "Which skill is the right one?",
      "criteria": {
        "gif-search": "Search and download GIFs from Tenor",
        "pdf": "Create, read, merge PDF files"
      }
    },
    "acts_on_user_system": {
      "type": "noul",
      "instructions": "Does this touch the user's system?"
    }
  }
}
```

**Response:**

```json
{
  "model": "laya-rl-agent",
  "answers": {
    "which": {
      "type": "choice",
      "choice": "gif-search",
      "probabilities": { "gif-search": 0.997, "pdf": 0.003 },
      "confidence": 0.997
    },
    "acts_on_user_system": {
      "type": "noul",
      "noul": 0.95
    }
  },
  "usage": {
    "input_tokens": 252,
    "output_tokens": 0,
    "state_tokens": 26
  },
  "routing": {
    "model": "english",
    "reason": "English Latin text"
  }
}
```

### `GET /health`

Returns loaded checkpoints, device info, and fallback counts.

---

## Architecture

```
laya-skill-router/
├── serve_laya.py          # Wrapper: raises MAX_CHOICE_OPTIONS, calls laya.serve
├── start-server.sh        # Bash launcher with env defaults
├── test_wire.py           # End-to-end test against the live server
├── probe.py               # Direct SDK probe (bypasses HTTP)
├── probe2.py              # Multi-request SDK probe
├── model/                  # Laya checkpoints (downloaded on first use)
│   ├── config.json
│   ├── model.safetensors
│   ├── tokenizer/
│   ├── multilingual/       # mmBERT-base (100+ languages)
│   └── typed-decisions/    # Fine-tuned on typed-decisions benchmark
└── .venv/                  # Python virtual environment
```

---

## Benchmarks

Measured on a Tesla T4, 17,416 questions, identical questions per model:

| Metric | Laya (routed) | TypeSafe Jev 1.13.0 |
|---|---|---|
| **typed-decisions accuracy** | **0.766** | 0.727 |
| **AG News accuracy** | **0.950** | 0.910 |
| **DAIR Emotion accuracy** | **0.595** | 0.480 |
| **ECE (calibration)** | **0.081** | 0.246 |
| **p50 latency (1 question)** | **32.8 ms** | 236–276 ms |
| **Languages usable** | **45 / 51** | — |
| **Cost** | **$0 self-hosted** | $0.042 / 1M tokens |

---

## License

[Apache 2.0](https://github.com/NandhaKishorM/laya/blob/main/LICENSE) — inherited from the Laya project.

---

## Acknowledgements

- [Laya](https://github.com/NandhaKishorM/laya) by NandhaKishorM — the decision model
- [ModernBERT](https://github.com/answerdotai/ModernBERT) — the backbone
- [Hermes Agent](https://hermes-agent.nousresearch.com) — the host platform
