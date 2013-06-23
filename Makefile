.PHONY: help test style docs view-docs coverage view-coverage

help:
	@echo "make help          - Show this text"
	@echo "make test          - Run the tests"
	@echo "make style         - Run pyflakes"
	@echo "make docs          - Build the docs"
	@echo "make view-docs     - Open the docs in a browser"
	@echo "make coverage      - Create a coverage report"
	@echo "make view-coverage - Open coverage report in a browser"

test: style
	python test_makestatic.py

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
