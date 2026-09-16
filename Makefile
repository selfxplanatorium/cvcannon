.PHONY: help setup templates profile doctor new build check privacy clean

PYTHON ?= python3

help:
	@$(PYTHON) scripts/cv.py help

setup:
	@bash scripts/setup.sh

templates:
	@$(PYTHON) scripts/cv.py templates

profile:
	@$(PYTHON) scripts/cv.py profile "$(TEMPLATE)"

doctor:
	@$(PYTHON) scripts/cv.py doctor

new:
	@$(PYTHON) scripts/cv.py new "$(SLUG)" "$(TEMPLATE)"

build:
	@$(PYTHON) scripts/cv.py build "$(SLUG)"

check:
	@$(PYTHON) scripts/cv.py check "$(SLUG)"

privacy:
	@$(PYTHON) scripts/privacy_check.py

clean:
	@$(PYTHON) scripts/cv.py clean "$(SLUG)"
