default: build

# Clean build, for releases.
release:
	ARCFLASH_PORT=none python3 build_and_upload.py

# Cached build, for development.
build:
	ARCFLASH_PORT=none ARCFLASH_CACHE=1 python3 build_and_upload.py

# Perform a clean build, then upload to connected board.
# TODO make this just upload.
upload:
	python3 build_and_upload.py
