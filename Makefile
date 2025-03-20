default: build

build:
	make -C os_switcher_bootloader
	make -C firmware
	cd tools && python3 make_arc_rom.py

release:
	make -C os_switcher_bootloader clean all
	make -C firmware release
	cd tools && python3 make_arc_rom.py

upload:
	make -C os_switcher_bootloader
	make -C firmware upload
	cd tools && python3 make_arc_rom.py upload
