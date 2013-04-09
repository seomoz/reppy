clean:
	# Remove the build
	sudo rm -rf build dist
	# And all of our pyc files
	find . -name '*.pyc' | xargs -n 100 rm
	# And lastly, .coverage files
	find . -name .coverage | xargs rm

nose:
	nosetests --exe --cover-package=reppy --with-coverage --cover-branches -v

test: nose
