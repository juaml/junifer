# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?="-W" "-E"
SPHINXBUILD   ?= sphinx-build
POLYBUILD     ?= sphinx-polyversion
SOURCEDIR     = .
# Output of the local (single version) build, relative to docs/
BUILDDIR      ?= _build
# Output of the multi-version build, relative to the repository root
POLYOUTDIR    ?= docs/_build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) --help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile clean local news _build_local html _html

clean:
	rm -rf $(BUILDDIR)/*
	rm -rf auto_examples/
	rm -rf api/generated/

# Build the docs of the working tree only
local:
	make _build_local; STATUS=$$?; exit $$STATUS

_build_local:
	$(SPHINXBUILD) "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# Build the docs of all the versions with sphinx-polyversion
html:
	make _html; STATUS=$$?; exit $$STATUS

_html:
	$(POLYBUILD) ./poly.py -vv -o OUTPUT_DIR="$(POLYOUTDIR)" -o SOURCE_DIR="./"

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	$(SPHINXBUILD) "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
