default: build upload

# Clean build, for releases.
release:
	python3 build.py

# Cached build, for development.
build:
	ARCFLASH_CACHE=1 python3 build.py

# Upload the last build.
upload:
	arcflash program-mcu firmware.ino.bin
