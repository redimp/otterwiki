all: run

.PHONY: clean coverage run debug shell sdist

clean:
	rm -rf venv *.egg-info dist *.log* otterwiki/__pycache__ tests/__pycache__
	rm -rf coverage_html

venv:
	python3 -m venv venv
	#venv/bin/python setup.py develop
	venv/bin/pip install -U pip
	venv/bin/pip install -e '.[dev]'

run: venv settings.cfg
	FLASK_APP=otterwiki.server OTTERWIKI_SETTINGS=../settings.cfg venv/bin/flask run --host 0.0.0.0

debug: venv settings.cfg
	FLASK_ENV=development FLASK_DEBUG=True FLASK_APP=otterwiki.server OTTERWIKI_SETTINGS=../settings.cfg venv/bin/flask run

shell: venv
	FLASK_DEBUG=True FLASK_APP=otterwiki.server OTTERWIKI_SETTINGS=../settings.cfg venv/bin/flask shell

test: venv
	OTTERWIKI_SETTINGS="" venv/bin/pytest tests

testpdb: venv
	OTTERWIKI_SETTINGS="" venv/bin/pytest --pdb tests


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
