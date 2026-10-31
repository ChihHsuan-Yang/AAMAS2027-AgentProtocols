# Reproduction targets for "Beyond Division of Labor".
#
#   make setup      create .venv and install the pinned analysis environment
#   make smoke      level A: offline tests + regenerate every post-freeze table
#                   from the committed intermediates; fails on any difference
#   make figures    regenerate every figure (fetches the Libertinus Sans font once)
#   make data       download the trajectories and the problem set, link them in place
#   make numbers    level B: re-derive every intermediate from the trajectories
#   make tables     regenerate every table, including the frozen-snapshot ones
#   make reproduce  numbers + tables + figures
#
# Nothing here calls a model endpoint. Re-running inference (level C) is
# documented in the README and is never triggered by make.

PYTHON ?= python3
VENV   ?= .venv
RUN    := $(shell [ -x "$(VENV)/bin/python" ] && echo "$(VENV)/bin/python" || echo "$(PYTHON)")
HF     := $(shell [ -x "$(VENV)/bin/hf" ] && echo "$(VENV)/bin/hf" || echo hf)

DATA_DIR     ?= data
HF_ROLES     ?= AgentsSci/AAMAS2027-Roles
HF_PROBLEMS  ?= AgentsSci/IEEE2026_BigData_MAS-4-Science-Matching
RELEASE_DIR  := analysis/hf_cache/release

# Figure font. Read from FONT_DIR, so no TeX installation is needed.
FONT_DIR       := .fonts
LIBERTINUS_URL := https://github.com/alerque/libertinus/releases/download/v7.040/Libertinus-7.040.zip

S := analysis/scripts

# CHECK=0 regenerates without diffing against the committed files (used when an
# input deliberately changed, e.g. after scripts/redact_release.py).
CHECK ?= 1
DIFF   = $(if $(filter 1,$(CHECK)),git diff --exit-code --stat --,@true)

# Tables generated from committed intermediates (analysis/out/FIGDATA_*.json).
POSTFREEZE_TABLES := mk_table_main mk_bf_replication mk_gate_table mk_robust_table mk_afs_table
FIGURES           := mk_fig_pipeline mk_fig1_bf mk_fig_supp

.DEFAULT_GOAL := help
.PHONY: help setup smoke fonts figures data validate-data numbers tables reproduce clean

help:
	@sed -n '3,11p' Makefile | sed 's/^# \{0,1\}//'

setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/python -m pip install --quiet --upgrade pip
	$(VENV)/bin/python -m pip install -r requirements.txt
	@echo "== setup: OK  (activate with: source $(VENV)/bin/activate)"

smoke:
	@echo "== offline checks of the RF and forced-submission conditions (no model calls)"
	$(RUN) experiments/test_bf_delivery.py
	$(RUN) experiments/test_afs.py
	@echo "== post-freeze tables from committed intermediates"
	@for s in $(POSTFREEZE_TABLES); do $(RUN) $(S)/$$s.py > /dev/null || exit 1; echo "  ok  $$s"; done
	git diff --exit-code --stat -- paper/tables
	@echo "== smoke: OK  (Table 2 and Tables S3-S6 reproduced byte for byte)"

fonts:
	@if [ ! -f $(FONT_DIR)/LibertinusSans-Regular.otf ]; then \
		mkdir -p $(FONT_DIR) && \
		curl -sSLf -o $(FONT_DIR)/libertinus.zip $(LIBERTINUS_URL) && \
		unzip -joq $(FONT_DIR)/libertinus.zip '*/static/OTF/LibertinusSans-*.otf' -d $(FONT_DIR) && \
		rm $(FONT_DIR)/libertinus.zip && echo "== fonts: Libertinus Sans in $(FONT_DIR)/"; \
	fi

figures: fonts
	@for s in $(FIGURES); do AAMAS_FONT_DIR=$(CURDIR)/$(FONT_DIR) $(RUN) $(S)/$$s.py > /dev/null || exit 1; echo "  ok  $$s"; done
	@echo "== figures written to paper/figures/; compare them visually or with git diff"

data:
	@command -v $(HF) >/dev/null 2>&1 || { echo "ERROR: 'hf' not found. Run: make setup"; exit 2; }
	$(HF) download $(HF_ROLES) --repo-type dataset --local-dir $(DATA_DIR)/roles
	$(HF) download $(HF_PROBLEMS) --repo-type dataset --local-dir $(RELEASE_DIR) \
	    --include "data/problems/*" --include "data/trajectories/*"
	$(MAKE) validate-data

validate-data:
	$(RUN) scripts/place_data.py --source $(DATA_DIR)

numbers:
	$(RUN) $(S)/FINAL_TABLES.py > analysis/out/FINAL_TABLES_OUTPUT.txt.tmp
	mv analysis/out/FINAL_TABLES_OUTPUT.txt.tmp analysis/out/FINAL_TABLES_OUTPUT.txt
	$(RUN) $(S)/bf_numbers.py > /dev/null
	$(RUN) $(S)/bf_numbers.py --bf-dir experiments/results/bf/chain2 --suffix _chain2 > /dev/null
	$(RUN) $(S)/bf_gate.py > /dev/null
	$(DIFF) analysis/out
	@echo "== numbers: OK$(if $(filter 1,$(CHECK)),  (every intermediate re-derived byte for byte),  (regenerated; not checked))"

tables:
	$(RUN) $(S)/mk_tables.py > /dev/null
	@for s in $(POSTFREEZE_TABLES); do $(RUN) $(S)/$$s.py > /dev/null || exit 1; done
	$(DIFF) paper/tables
	@echo "== tables: OK$(if $(filter 1,$(CHECK)),  (every table reproduced byte for byte),  (regenerated; not checked))"

reproduce: numbers tables figures

clean:
	rm -rf figures/*.pdf figures/*.png
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
