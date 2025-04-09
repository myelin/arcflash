default: build upload

clean:
	rm -rf build_output_*

# Clean build, for releases.
release: clean
	python3 build.py
	cp firmware.ino.bin ../python_lib/arcflash/firmware.bin

# Cached build, for development.
build:
	ARCFLASH_CACHE=1 python3 build.py --dev
	cp firmware.ino.bin ../python_lib/arcflash/firmware.bin

# Upload the last build.
upload:
	arcflash program-mcu firmware.ino.bin
