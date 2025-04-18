#include "arcflash.h"
#include "host_mcu_comms.h"

// Just print bytes received from the serial channel (for debugging with Arculator).
// #define SERIAL_JUST_PRINT

void test_cmos_rw() {
    display_printf("Testing reading and writing CMOS.\n");

    uint8_t initial_data[256];
    read_cmos(initial_data);

    uint8_t expected_data[256];
    read_cmos(expected_data);

    // We don't have rand(), so just write sequential numbers.
    uint8_t counter = 1;

    bool fail = false;

    for (int addr = 16; addr < 256; ++addr) {
        display_printf("Testing from addr %d...\n", addr);
        for (int bytes_to_write = 1; bytes_to_write <= 256 - addr; ++bytes_to_write) {
            // Generate test data
            for (int pos = addr; pos < addr + bytes_to_write; ++pos) {
                expected_data[pos] = counter++;
            }
            // Write it
            write_cmos(addr, bytes_to_write, expected_data + addr);
            // Read back
            uint8_t data[256];
            read_cmos(data);
            // Compare
            bool diff = false;
            for (int i = 16; i < 256; ++i) {
                if (data[i] != expected_data[i]) {
                    diff = true;
                }
            }
            if (diff) fail = true;
            display_printf("%sWrote %d bytes from %d, %s\n",
                fail ? "FAIL " : "",
                bytes_to_write, addr, diff ? "MISMATCH" : "match");

            // for (int i = 16; i < 256; ++i) {
            //     display_printf(" %02X", data[i]);
            // }
            // display_printf("\n");
        }
    }
}

void test_mcu_comms() {
    display_printf("Testing communications with the MCU.\n");

    const int buffer_size = 8000;
    uint8_t test_buffer[buffer_size];
    const int response_buffer_size = 10240;
    uint8_t response_buffer[response_buffer_size];

    for (int i = 0; i < 100; ++i) {
        size_t packet_size = (i * 500) % buffer_size;
        display_printf("Sending packet %d (%d B)\n", i, packet_size);
        // Fill the test buffer.
        for (size_t x = 0; x < packet_size; ++x) {
            test_buffer[x] = (i + (x * 10)) & 0xFF;
        }
        // Send a ping packet to the MCU.
        host_mcu_comms::transmit_packet(host_mcu_comms::kMsgTestPing,
                                        test_buffer, packet_size);
        // Wait for a response.
#ifdef SERIAL_JUST_PRINT
        int pos = 0, frame_errors = 0;
        for (; pos < 100; ++pos) {
            uint32_t c = read_serial_byte();
            if (c == SERIAL_TIMEOUT) {
                display_printf("Timeout after %d bytes\n", pos);
                break;
            }
            if (c & SERIAL_FRAMING_ERROR) ++frame_errors;
            response_buffer[pos] = (uint8_t)c;
        }
        display_printf("Received %d bytes with %d framing errors\n", pos,
                       frame_errors);
        for (int x = 0; x < pos; ++x) {
            display_printf(" %02X", response_buffer[x]);
        }
        display_printf("\n");
        while (1);  // Stop here, to make the Arculator logs easier to read.
#else
        host_mcu_comms::PacketReceiver packet_receiver(response_buffer,
                                                       response_buffer_size);
        bool done = false;
        while (!done) {
            uint32_t c = read_serial_byte();
            if (c > 0xFF) {
                if (c == SERIAL_TIMEOUT) {
                    display_printf("Response %d: serial timeout\n", i);
                } else if (c & SERIAL_FRAMING_ERROR) {
                    display_printf("Response %d: serial framing error (%X)\n",
                                   i, c);
                } else {
                    display_printf("Response %d: unknown error reading byte\n",
                                   i);
                }
                break;
            }
            switch (packet_receiver.process_received_byte((uint8_t)c)) {
                case host_mcu_comms::ProcessReceivedByteResponse::OK:
                    break;
                case host_mcu_comms::ProcessReceivedByteResponse::FAIL:
                    display_printf("Response %d failed!\n", i);
                    done = true;
                    break;
                case host_mcu_comms::ProcessReceivedByteResponse::
                    PACKET_RECEIVED:
                    display_printf(
                        "Response %d (%X) received successfully (%d B).\n", i,
                        packet_receiver.packet_type(), packet_receiver.size());
                    size_t compare_size = packet_size;
                    if (packet_receiver.size() != packet_size) {
                        display_printf("Packet size mismatch\n");
                        compare_size = packet_receiver.size();
                    }
                    bool match = true;
                    for (size_t i = 0; i < compare_size; ++i) {
                        if (test_buffer[i] != packet_receiver.message()[i])
                            match = false;
                    }
                    if (!match) {
                        display_printf("Packet contents mismatch\n");
                    }
                    done = true;
                    break;
            }
        }
#endif
    }
}


void run_tests() {
    display_printf("Running Arcflash tests...\n");

    test_cmos_rw();
    test_mcu_comms();
}
