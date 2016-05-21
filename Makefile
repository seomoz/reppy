.PHONY: test
test:
	nosetests --with-coverage

install:
	python setup.py install

dev-requirements:
	pip freeze | grep -v -e reppy > dev-requirements.txt

dev-requirements-py3:
	pip freeze | grep -v -e reppy > dev-requirements-py3.txt

clean:
	rm -rf build dist *.egg-info
	find . -name '*.pyc' | xargs --no-run-if-empty rm
