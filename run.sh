#!/bin/bash
uvicorn apiserver:app --host 0.0.0.0 --port 8000 --reload --limit-concurrency 5 --workers 1
