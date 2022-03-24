# Makefile before PR
#

.PHONY: checks

checks: flake spellcheck

flake:
	flake8

spellcheck:
	codespell junifer/ docs/ examples/

test:
	pytest -vv --cov=junifer --cov-report html --cov-report term