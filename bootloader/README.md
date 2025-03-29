# Bootloader for Arcflash ATSAMD21E18A

This is the bootloader for the Arcflash's MCU, built from [github.com/myelin/uf2-samdx1](https://github.com/myelin/uf2-samdx1).

To program into a freshly made or unresponsive Arcflash:

~~~
python3 -m pip install --user https://github.com/adafruit/Adafruit_Adalink/archive/master.zip
python3 -m adalink.main -v atsamd21g18 -p jlink -w -h bootloader-*.bin
~~~

To program into an Arcflash with a working bootloader, [install arduino-cli](https://arduino.github.io/arduino-cli/installation/) and run the following:

~~~
cp update-bootloader-*.ino bootloader.ino
arduino-cli compile --verbose --fqbn arduino:samd:adafruit_circuitplayground_m0
# Use /dev/ttyACM* (Linux) or COMn (Windows) here:
arduino-cli upload --verbose --fqbn arduino:samd:adafruit_circuitplayground_m0 --port /dev/tty.usbmodem*
~~~

To rebuild:

~~~
make clean build
~~~

To erase an unresponsive Arcflash, try this.  The `erase` command by itself won't work, as the UF2
bootloader locks the first 0x2000 bytes.

~~~
JLinkExe -device ATSAMD21G18 -if swd -speed 1000
connect
erase 0x2000,0x40000
~~~
