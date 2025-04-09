default: test build

.PHONY: default build test clean release upload

# Local dev build.
build:
	make -C os_switcher_bootloader build
	make -C firmware build
	cd tools && python3 make_arc_rom.py

test:
	make -C host_mcu_comms test
	make -C cpld test

clean:
	make -C os_switcher_bootloader clean
	make -C firmware clean

# Release build, run on GitHub.
release:
	# Build everything
	make -C os_switcher_bootloader release
	make -C firmware release
	# And run tests
	make -C host_mcu_comms test

# Local dev build + push to connected device.
upload:
	make -C host_mcu_comms
	make -C os_switcher_bootloader
	make -C firmware upload
	cd tools && python3 make_arc_rom.py upload
