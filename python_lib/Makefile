.PHONY: build clean

default: build

build:
	pip wheel .
	tar -tzf arcflash*.whl

dev:
	pip install -e .

clean:
	rm -rf *.whl arcflash.egg-info build */arcflash.egg-info */*.so
