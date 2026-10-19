# Thin wrapper: every target delegates to tasks.py so Windows users get the same
# behaviour with `python tasks.py <task>`.
PY ?= python3

.PHONY: setup up lint test openapi reproduce demo
setup up lint test openapi reproduce demo:
	$(PY) tasks.py $@
