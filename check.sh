#!/bin/sh
# The project's whole check: every test, with Python's standard library only. Runs in the
# check container (python:3.15-slim) without a network, and on any machine with Python 3.12+.
set -eu
cd "$(dirname "$0")"
exec python3 -B -m unittest discover --start-directory tests --verbose
