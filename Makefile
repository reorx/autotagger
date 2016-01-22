.PHONY: clean test

clean:
	rm -rf build dist *.egg-info

test:
	PYTHONPATH=. nosetests -w test/ -v

publish:
	python setup.py sdist upload

publish-all:
	python setup.py sdist bdist_wheel upload

compress-image:
	cd images && ls origin*.png | xargs -L 1 -I{} convert {} -resize 50% -sharpen  0x0.55+0.55+0.008 r-{}
