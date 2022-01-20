# Makefile before PR
#

.PHONY: checks

checks: flake spellcheck

flake:
	flake8

spellcheck:
	codespell <PKG_NAME>/ docs/ examples/

test:
	pytest -v