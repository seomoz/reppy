.PHONY: test
test: reppy/robots.so
	nosetests --with-coverage tests

test-docker:
	docker build -t reppy-tests . && docker run --rm reppy-tests
	docker rmi reppy-tests

reppy/%.so: reppy/%.py* reppy/rep-cpp/src/* reppy/rep-cpp/include/* reppy/rep-cpp/deps/url-cpp/include/* reppy/rep-cpp/deps/url-cpp/src/*
	python setup.py build_ext --inplace

install:
	python setup.py install

dev-requirements:
	pip freeze | grep -v -e reppy > dev-requirements.txt

clean:
	rm -rf build dist *.egg-info reppy/*.so
	find . -name '*.pyc' | xargs --no-run-if-empty rm
