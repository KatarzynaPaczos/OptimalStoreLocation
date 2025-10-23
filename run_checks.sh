#!/usr/bin/env bash
vulture src/ main.py data/
ruff check . --fix
ruff check . --select E,W,F --line-length 120 --fix
