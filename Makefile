.PHONY: test style docs view-docs coverage view-coverage

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
