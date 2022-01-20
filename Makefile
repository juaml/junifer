# Makefile before PR
#

.PHONY: checks

checks: flake spellcheck

flake:
	flake8

spellcheck:
	codespell junifer/ docs/ examples/

test:
	pytest -v