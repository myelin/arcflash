# Firmware for Arcflash ATSAMD21E18A

This is the code that runs on the Arcflash's MCU.

It's built using the Arduino toolchain; originally using the Adafruit Circuit Playground Express variant, but now we have our own variant (see the hardware folder for details).

To build and upload, you'll need to [install arduino-cli](https://arduino.github.io/arduino-cli/installation/).

macOS: `brew install arduino-cli`

Ubuntu: `sudo apt install make; sudo snap install arduino-cli`

Run `make` for an incremental build or `make release` for a clean build.

Run `make upload` to build the code and upload it to a connected Arcflash board.

If you see "Platform not installed", "Error resolving FQBN", or an error finding a tool like `arm-none-eabi-g++`, update your cores:

~~~
arduino-cli --config-file arduino-cli.yaml core update-index
arduino-cli --config-file arduino-cli.yaml core install adafruit:samd
~~~

If you see linker errors ("Undefined reference to \`Uart::Uart(SERCOM\*, ...") on Windows, just rerun build_and_upload.py; this just seems to happen sometimes (?!)

> (2021-01-19) Note that arduino-cli 0.14.0 has a bug (*"Error during Upload: uploading error: cannot execute upload tool: fork/exec {runtime.tools.bossac-1.7.0-arduino3.path}/bossac: no such file or directory"* when it tries to upload the compiled code to the board), so if 0.15.0 isn't out yet, you'll need to:
>
> - On Windows and Linux, install a nightly build from the [arduino-cli site](https://arduino.github.io/arduino-cli/installation/)
> - On macOS, install from HEAD using Homebrew: `brew install --HEAD arduino-cli`

