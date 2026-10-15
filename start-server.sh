#!/usr/bin/env bash
# Local Laya decision server for the Hermes laya-skill-router plugin.
# Speaks TypeSafe's /v1/systemone wire protocol, so any Jev client works unchanged.
cd "$(dirname "$0")" || exit 1
export LAYA_HOST="${LAYA_HOST:-127.0.0.1}"
export LAYA_PORT="${LAYA_PORT:-8100}"
export LAYA_DEVICE="${LAYA_DEVICE:-cpu}"
export LAYA_MODELS="${LAYA_MODELS:-english}"
export LAYA_PRELOAD="${LAYA_PRELOAD:-1}"
export LAYA_MAX_LOADED="${LAYA_MAX_LOADED:-1}"
export LAYA_DEFAULT_MODEL="${LAYA_DEFAULT_MODEL:-english}"
export LAYA_ROSTER_CAP="${LAYA_ROSTER_CAP:-250}"
exec ./.venv/Scripts/python.exe serve_laya.py
