.PHONY: help dev test test-all style docs view-docs coverage view-coverage

help:
	@echo "make help          - Show this text"
	@echo "make dev           - Install development dependencies"
	@echo "make test          - Run the tests"
	@echo "make test-all      - Run the tests on all supported Python versions"
	@echo "make style         - Run pyflakes"
	@echo "make docs          - Build the docs"
	@echo "make view-docs     - Open the docs in a browser"
	@echo "make coverage      - Create a coverage report"
	@echo "make view-coverage - Open coverage report in a browser"

dev:
	pip install -r dev-requirements.txt
	pip install --editable .

test: style
	python test_makestatic.py

test-all:
	tox

style:
	find flask_makestatic test_makestatic.py setup.py -iname "*.py" | xargs pyflakes

docs:
	make -C docs html

view-docs: docs
	open docs/_build/html/index.html

coverage:
	coverage run --source=flask_makestatic test_makestatic.py

view-coverage: coverage
	coverage html
	open htmlcov/index.html
