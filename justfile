default:
    just --list

install-prek:
    uv tool install prek

install-hooks:
    prek install --install-hooks

run-hooks:
    prek run --all-files

install-dev:
    uv pip install -e ".[dev,docs,all]"

format-lint:
    uv run -- ruff format . && ruff check --fix .

serve-docs:
    uv run -- sphinx-autobuild docs docs/_build

lint:
    uv run -- tox -e ruff

changelog:
    uv run -- tox -e changelog

add-news news id type:
    uv run -- towncrier create -c "{{news}}" {{id}}.{{type}}
