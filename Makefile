.PHONY: test docs view-docs

test:
	python test_makestatic.py

docs:
	make -C docs html

view-docs: docs
	open docs/_build/html/index.html
