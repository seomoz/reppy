.PHONY: test
test: reppy/robots.so
	nosetests --with-coverage tests

reppy/%.so: reppy/%.py* reppy/rep-cpp/src/* reppy/rep-cpp/include/* reppy/rep-cpp/deps/url-cpp/include/* reppy/rep-cpp/deps/url-cpp/src/*
	python setup.py build_ext --inplace

install:
	python setup.py install

dev-requirements:
	pip freeze | grep -v -e reppy > dev-requirements.txt

dev-requirements-py3:
	pip freeze | grep -v -e reppy > dev-requirements-py3.txt

clean:
	rm -rf build dist *.egg-info reppy/*.so
	find . -name '*.pyc' | xargs --no-run-if-empty rm
