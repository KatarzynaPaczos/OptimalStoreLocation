#!/usr/bin/env bash
VENV_PY=./.venv/Scripts/python

$VENV_PY -m vulture app/
$VENV_PY -m vulture main.py
$VENV_PY -m ruff check app/
$VENV_PY -m ruff check . --fix
$VENV_PY -m ruff check .