PORT ?= 8080
VERSION := $(shell python3 -c "with open('otterwiki/version.py') as f: exec(f.read());  print(__version__);")
PLATFORM ?= "linux/arm64,linux/amd64,linux/arm/v7,linux/arm/v6"

all: run

.PHONY: clean coverage run debug shell sdist docker-build docker-test

clean:
	rm -rf venv *.egg-info dist *.log* otterwiki/__pycache__ tests/__pycache__
	rm -rf .pytest_cache .tox
	rm -rf coverage_html

venv:
	python3 -m venv venv
	#venv/bin/python setup.py develop
	venv/bin/pip install -U pip wheel
	venv/bin/pip install -e '.[dev]'

run: venv settings.cfg
	FLASK_APP=otterwiki.server OTTERWIKI_SETTINGS=$(PWD)/settings.cfg venv/bin/flask run --host 0.0.0.0 --port $(PORT)

debug: venv settings.cfg
	FLASK_ENV=development FLASK_DEBUG=True FLASK_APP=otterwiki.server OTTERWIKI_SETTINGS=../settings.cfg venv/bin/flask run --port $(PORT)

shell: venv
	FLASK_DEBUG=True FLASK_APP=otterwiki.server OTTERWIKI_SETTINGS=../settings.cfg venv/bin/flask shell

test: venv
	OTTERWIKI_SETTINGS="" venv/bin/pytest tests

testpdb: venv
	OTTERWIKI_SETTINGS="" venv/bin/pytest --pdb tests

tox: venv
	# TODO: autodected available python versions and set TOXENV=py37,py39,..
	venv/bin/tox

venv/bin/coverage: venv
	venv/bin/pip install coverage

coverage: venv venv/bin/coverage
	OTTERWIKI_SETTINGS="" venv/bin/coverage run --source=otterwiki -m pytest tests
	venv/bin/coverage report
	venv/bin/coverage html -d coverage_html

black:
	venv/bin/black setup.py otterwiki/ tests/

sdist: venv test
	venv/bin/python setup.py sdist

settings.cfg:
	@echo ""
	@echo " Please create the settings.cfg. You find an example in the"
	@echo " settings.cfg.skeleton"
	@echo ""
	@false

docker-test:
	# make sure the image is rebuild
	DOCKER_BUILDKIT=1 docker rmi otterwiki:_test || true
	DOCKER_BUILDKIT=1 docker build -t otterwiki:_test --target test-stage .

docker-build: docker-test
	DOCKER_BUILDKIT=1 docker build -t otterwiki:_build .

docker-run:
	DOCKER_BUILDKIT=1 docker build -t otterwiki:_build .
	docker run -p 8080:80 otterwiki:_build

docker-buildx-test:
	docker buildx build --platform $(PLATFORM) --target test-stage .

docker-buildx-push: venv
# check if we are in the main branch (to avoid accidently pushing a feature branch
ifneq ($(strip $(shell git rev-parse --abbrev-ref HEAD)),main)
	$(error Error: Not on branch 'main')
endif
# check if git is clean optional: --untracked-files=no
# reconsider if -t redimp/otterwiki:$(shell git describe --tags) might be useful
ifneq ($(strip $(shell git status --porcelain)),)
	$(error Error: Uncommitted changes in found)
endif
	docker buildx build --platform $(PLATFORM) -t redimp/otterwiki:latest -t redimp/otterwiki:$(VERSION)  . --push
