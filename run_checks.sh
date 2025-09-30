#!/usr/bin/env bash
vulture src/
vulture main.py
ruff check src/
ruff check . --fix
ruff check .