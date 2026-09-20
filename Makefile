.PHONY: help setup templates profile doctor portrait-convert new build check privacy clean \
	docker-setup docker-image docker-templates docker-profile docker-doctor \
	docker-portrait-convert docker-new docker-build docker-check docker-privacy docker-clean

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

portrait-convert:
	@$(PYTHON) scripts/cv.py portrait-convert

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

docker-setup:
	@bash docker-setup.sh

docker-image:
	@docker compose build

docker-templates:
	@scripts/docker.sh make templates

docker-profile:
	@scripts/docker.sh make profile TEMPLATE="$(TEMPLATE)"

docker-doctor:
	@scripts/docker.sh make doctor

docker-portrait-convert:
	@scripts/docker.sh make portrait-convert

docker-new:
	@scripts/docker.sh make new SLUG="$(SLUG)" TEMPLATE="$(TEMPLATE)"

docker-build:
	@scripts/docker.sh make build SLUG="$(SLUG)"

docker-check:
	@scripts/docker.sh make check SLUG="$(SLUG)"

docker-privacy:
	@scripts/docker.sh make privacy

docker-clean:
	@scripts/docker.sh make clean SLUG="$(SLUG)"
