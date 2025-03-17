#!/bin/bash
set -euo pipefail

# Syntax: $0 /path/to/ArduinoCore-samd

# In my case: ./update_from_upstream.sh ~/Dropbox/projects/arduino-samd/adafruit-ArduinoCore-samd

SRC=$1
DEST=samd

# Copy platform.txt and change name.
sed -e 's/name=Adafruit SAMD.*/name=Myelin SAMD Boards (based on Adafruit SAMD)/' "$SRC/platform.txt" > "$DEST/platform.txt"

# Copy circuitplayground_m0 definition out of boards.txt and rename to arcflash.
grep circuitplay "$SRC/boards.txt" | sed -e 's/adafruit_circuitplayground_m0/arcflash/' > $DEST/boards.txt

# Copy Arduino core and the libraries we use.
for path in cores/arduino libraries/Adafruit_ZeroDMA libraries/SPI libraries/Wire; do
	rm -rf $DEST/$path
	cp -av $SRC/$path $DEST/$path
	rm -rf $DEST/$path/{.git*,examples}
	git add $DEST/$path
done

git status -- .

echo "Please double check any changes to $DEST/boards.txt, as this script will have undone many necessary changes for Arcflash."
