rebuild:
	make -C 32kb_flash_cartridge/pcb-common rebuild
	make -C atsamd11_pro_micro/pcb rebuild
	make -C cpu_socket_expansion/pcb rebuild
	make -C cpu_socket_minispartan_daughterboard/pcb rebuild
	make -C elk_pi_tube_direct/pcb rebuild
	make -C master_updateable_megarom/pcb rebuild
	make -C minus_one/pcb rebuild
	make -C serial_sd_adapter/bbc_1mhz_bus_pcb rebuild
	make -C standalone_cartridge_programmer/pcb rebuild
