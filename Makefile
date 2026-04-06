#
#
# Makefile for developing and building An Otter Wiki
#
# Please read the Installation guide <https://otterwiki.com/Installation>
# to get started.
#
#
PORT ?= 8080
VERSION := $(shell python3 -c "with open('otterwiki/version.py') as f: exec(f.read());  print(__version__);")
VERSION_MAJOR_MINOR := $(shell python3 -c "with open('otterwiki/version.py') as f: exec(f.read()); print('.'.join(__version__.split('.')[0:2]));")
VERSION_MAJOR := $(shell python3 -c "with open('otterwiki/version.py') as f: exec(f.read()); print('.'.join(__version__.split('.')[0:1]));")
PLATFORM ?= "linux/arm64,linux/amd64,linux/arm/v7,linux/arm/v6"
PLATFORM_QUICK ?= "linux/arm64,linux/amd64"
HELM_VERSION := $(shell grep ^version helm/Chart.yaml | awk '{print $$2}')

# Detect OS and set venv binary path accordingly
ifeq ($(OS),Windows_NT)
	VENVBIN := venv/Scripts
else
	VENVBIN := venv/bin
endif

all: run

.PHONY: clean coverage run debug cli shell sdist docker-build docker-test
ARGS ?=

clean:
	rm -rf venv *.egg-info dist *.log* otterwiki/__pycache__ tests/__pycache__
	rm -rf .pytest_cache .tox
	rm -rf coverage_html

venv: pyproject.toml
	rm -rf venv
	python3 -m venv venv
	$(VENVBIN)/python3 -m pip install -U pip wheel
	$(VENVBIN)/pip install -e '.[dev]'
	$(VENVBIN)/pre-commit install

run: venv settings.cfg
	GIT_TAG=$(shell git describe --long) FLASK_APP=otterwiki.server OTTERWIKI_SETTINGS=$(PWD)/settings.cfg $(VENVBIN)/flask run --host 0.0.0.0 --port $(PORT)

debug: venv settings.cfg
	FLASK_ENV=development FLASK_DEBUG=True FLASK_APP=otterwiki.server OTTERWIKI_SETTINGS=../settings.cfg $(VENVBIN)/flask run --port $(PORT)

cli: venv settings.cfg
	FLASK_APP=otterwiki.server OTTERWIKI_SETTINGS=$(PWD)/settings.cfg $(VENVBIN)/flask $(ARGS)

profiler: venv settings.cfg
	FLASK_DEBUG=True FLASK_APP=otterwiki.server OTTERWIKI_SETTINGS=../settings.cfg \
		$(VENVBIN)/python otterwiki/profiler.py


shell: venv
	FLASK_DEBUG=True FLASK_APP=otterwiki.server OTTERWIKI_SETTINGS=../settings.cfg $(VENVBIN)/flask shell

test: venv
	OTTERWIKI_SETTINGS="" $(VENVBIN)/pytest tests

tox: venv
	$(VENVBIN)/tox

coverage: venv
	OTTERWIKI_SETTINGS="" $(VENVBIN)/coverage run --source=otterwiki -m pytest tests
	$(VENVBIN)/coverage report
	$(VENVBIN)/coverage html

black:
	$(VENVBIN)/black setup.py otterwiki/ tests/

sdist: venv test
	$(VENVBIN)/python setup.py sdist

settings.cfg:
	@echo ""
	@echo " Please create the settings.cfg. You find an example in the"
	@echo " settings.cfg.skeleton"
	@echo ""
	@false

tmp/codemirror-5.65.15:
	mkdir -p tmp && \
	cd tmp && \
	test -f codemirror.zip || wget https://codemirror.net/5/codemirror.zip && \
	unzip codemirror.zip

otterwiki/static/js/cm-modes.min.js: Makefile tmp/codemirror-5.65.15
	cat tmp/codemirror-5.65.15/addon/mode/simple.js > otterwiki/static/js/cm-modes.js
	cat tmp/codemirror-5.65.15/mode/meta.js >> otterwiki/static/js/cm-modes.js
	for MODE in shell clike xml python javascript markdown yaml php sql \
		toml cmake perl http go rust dockerfile powershell properties \
		stex nginx haskell lua jinja2 ruby; do \
		cat tmp/codemirror-5.65.15/mode/$$MODE/$$MODE.js \
			>> otterwiki/static/js/cm-modes.js; \
	done
	./$(VENVBIN)/python -m rjsmin -p < otterwiki/static/js/cm-modes.js > otterwiki/static/js/cm-modes.min.js

docker-test:
	# make sure the image is rebuild
	docker build -t otterwiki:_test --target test-stage .
	docker run -it --rm otterwiki:_test

docker-run:
	docker build -t otterwiki:_build .
	docker run -p 8080:80 otterwiki:_build

docker-run-slim:
	docker build -t otterwiki:_build-slim \
		-f docker/Dockerfile.slim \
		.
	docker run -p 8080:8080 otterwiki:_build-slim

docker-platform-test:
ifeq ($(strip $(shell git rev-parse --abbrev-ref HEAD)),main)
	docker buildx build --platform $(PLATFORM) --target test-stage .
else
	docker buildx build --platform $(PLATFORM_QUICK) --target test-stage .
endif

docker-push-slim: test
ifeq ($(strip $(shell git rev-parse --abbrev-ref HEAD)),main)
# check if git is clean
ifneq ($(strip $(shell git status --porcelain)),)
	$(error Error: Uncommitted changes in found)
endif
	docker buildx build \
		--platform $(PLATFORM) \
		-f docker/Dockerfile.slim \
		-t redimp/otterwiki:$(VERSION)-slim \
		-t redimp/otterwiki:$(VERSION_MAJOR)-slim \
		-t redimp/otterwiki:$(VERSION_MAJOR_MINOR)-slim \
		--build-arg GIT_TAG="$(shell git describe --long)" \
		--push .
else
	@echo ""
	@echo "-- Building dev image"
	@echo ""
	docker buildx build --platform $(PLATFORM_QUICK) \
		-f docker/Dockerfile.slim \
		-t redimp/otterwiki:dev-$(shell git rev-parse --abbrev-ref HEAD)-slim \
		--build-arg GIT_TAG="$(shell git describe --long)_$(shell git rev-parse --abbrev-ref HEAD)" \
		--push .
	@echo ""
	@echo "-- Done dev-image: redimp/otterwiki:dev-$(shell git rev-parse --abbrev-ref HEAD)-slim"
	@echo ""
endif

docker-push: test
# check if we are in the main branch (to avoid accidentally pushing a feature branch
ifeq ($(strip $(shell git rev-parse --abbrev-ref HEAD)),main)
# check if git is clean
ifneq ($(strip $(shell git status --porcelain)),)
	$(error Error: Uncommitted changes in found)
endif
	docker buildx build --platform $(PLATFORM) \
		-t redimp/otterwiki:latest \
		-t redimp/otterwiki:$(VERSION) \
		-t redimp/otterwiki:$(VERSION_MAJOR) \
		-t redimp/otterwiki:$(VERSION_MAJOR_MINOR) \
		--build-arg GIT_TAG="$(shell git describe --long)" \
		--push .
else
	@echo ""
	@echo "-- Building dev image"
	@echo ""
	docker buildx build --platform $(PLATFORM_QUICK) \
		-t redimp/otterwiki:dev-$(shell git rev-parse --abbrev-ref HEAD) \
		--build-arg GIT_TAG="$(shell git describe --long)_$(shell git rev-parse --abbrev-ref HEAD)" \
		--push .
	@echo ""
	@echo "-- Done dev-image: redimp/otterwiki:dev-$(shell git rev-parse --abbrev-ref HEAD)"
	@echo ""
endif

pypi: test
	./$(VENVBIN)/python3 -m pip install --upgrade build twine
	./$(VENVBIN)/python3 -m build
	./$(VENVBIN)/python3 -m twine upload -r pypi dist/*

helm-build:
	cd helm/ && helm lint ./
	cd helm/ && helm package ./

helm-test:
	cd helm/ && \
	helm template otterwiki \
		--set config.SITE_NAME=Template \
		./

helm-push: helm-build
	set -e; \
	CHARTS_POD=$$(kubectl get pods -n 'otterwiki' -l 'app.kubernetes.io/name=charts-otterwiki-com' -o jsonpath='{.items[0].metadata.name}'); \
	kubectl cp -c chartexhibiton helm/otterwiki-$(HELM_VERSION).tgz otterwiki/$$CHARTS_POD:/data; \
	kubectl rollout restart deployment -n otterwiki -l app.kubernetes.io/name=charts-otterwiki-com
