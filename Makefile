all: run

clean:
	rm -rf venv && rm -rf *.egg-info && rm -rf dist && rm -rf *.log* && rm -rf otterwiki/__pycache__

venv:
	virtualenv --python=python3 venv
	venv/bin/pip install -r requirements.txt
	venv/bin/python setup.py develop

run: venv
	FLASK_APP=otterwiki OTTERWIKI_SETTINGS=../settings.cfg venv/bin/flask run --host 0.0.0.0

debug: venv
	FLASK_ENV=development FLASK_DEBUG=True FLASK_APP=otterwiki OTTERWIKI_SETTINGS=../settings.cfg venv/bin/flask run

shell: venv
	FLASK_DEBUG=True FLASK_APP=otterwiki OTTERWIKI_SETTINGS=../settings.cfg venv/bin/flask shell

test: venv
	OTTERWIKI_SETTINGS="" venv/bin/python -m unittest discover -s tests

venv/bin/coverage: venv
	venv/bin/pip install coverage

coverage: venv venv/bin/coverage
	OTTERWIKI_SETTINGS="" venv/bin/coverage run --source=otterwiki -m unittest discover -s tests
	venv/bin/coverage report
	venv/bin/coverage html -d coverage_html

sdist: venv test
	venv/bin/python setup.py sdist
