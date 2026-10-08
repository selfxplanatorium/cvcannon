.PHONY: help setup templates profile doctor portrait-convert new build check build-all check-all \
	privacy tools clean clean-all \
	docker-setup docker-image docker-templates docker-profile docker-doctor \
	docker-portrait-convert docker-new docker-build docker-check docker-build-all docker-check-all \
	docker-privacy docker-clean docker-clean-all

ifeq ($(OS),Windows_NT)
PYTHON ?= python
else
PYTHON ?= python3
endif
CV = @$(PYTHON) scripts/cv.py

help:
	$(CV) help

setup:
	$(CV) setup

templates:
	$(CV) templates

profile:
	$(CV) profile "$(TEMPLATE)"

doctor:
	$(CV) doctor

portrait-convert:
	$(CV) portrait-convert

new:
	$(CV) new "$(SLUG)" "$(TEMPLATE)"

build:
	$(CV) build "$(SLUG)"

check:
	$(CV) check "$(SLUG)"

build-all:
	$(CV) build-all

check-all:
	$(CV) check-all

tools:
	$(CV) tools

privacy:
	$(CV) privacy

clean:
	$(CV) clean "$(SLUG)"

clean-all:
	$(CV) clean-all

docker-setup:
	$(CV) docker-setup

docker-image:
	$(CV) docker-image

docker-templates:
	$(CV) docker-templates

docker-profile:
	$(CV) docker-profile "$(TEMPLATE)"

docker-doctor:
	$(CV) docker-doctor

docker-portrait-convert:
	$(CV) docker-portrait-convert

docker-new:
	$(CV) docker-new "$(SLUG)" "$(TEMPLATE)"

docker-build:
	$(CV) docker-build "$(SLUG)"

docker-check:
	$(CV) docker-check "$(SLUG)"

docker-build-all:
	$(CV) docker-build-all

docker-check-all:
	$(CV) docker-check-all

docker-privacy:
	$(CV) docker-privacy

docker-clean:
	$(CV) docker-clean "$(SLUG)"

docker-clean-all:
	$(CV) docker-clean-all
