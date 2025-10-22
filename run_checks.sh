#!/usr/bin/env bash
vulture src/
vulture main.py
vulture data/
ruff check src/
ruff check data/
ruff check . --fix
ruff check .
