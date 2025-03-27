default: test build

build:
	make -C os_switcher_bootloader build
	make -C firmware build
	cd tools && python3 make_arc_rom.py

test:
	make -C host_mcu_comms test
	make -C cpld test2

release:
	make -C host_mcu_comms
	make -C os_switcher_bootloader clean all
	make -C firmware release
	cd tools && python3 make_arc_rom.py

upload:
	make -C host_mcu_comms
	make -C os_switcher_bootloader
	make -C firmware upload
	cd tools && python3 make_arc_rom.py upload
