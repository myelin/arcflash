default: test

test:
	mkdir -p debug
	g++ \
		-std=c++17 \
		-Wall \
		-Werror \
		-DTESTING \
		-o debug/host_mcu_comms_test \
		-I../third_party/crc32 \
		*.cc \
		../third_party/crc32/*.cc
	debug/host_mcu_comms_test
