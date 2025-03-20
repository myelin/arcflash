#include "host_mcu_comms.h"

#include <stddef.h>
#include <stdio.h>
#include <string.h>

constexpr size_t buffer_size = 1024;
uint8_t buffer[buffer_size];
host_mcu_comms::PacketReceiver packet_receiver(buffer, buffer_size);
bool fail_received = false;

// Fake byte transmitter that just passes bytes straight to packet_receiver.
bool host_mcu_comms::transmit_byte(uint8_t tx_byte) {
    printf("tx %02x (%c)\n", tx_byte,
           (tx_byte >= 32 && tx_byte <= 127) ? tx_byte : '?');
    switch (packet_receiver.process_received_byte(tx_byte)) {
        case ProcessReceivedByteResponse::OK:
            break;
        case ProcessReceivedByteResponse::FAIL:
            printf("FAIL received when processing byte!\n");
            fail_received = true;
            break;
        case ProcessReceivedByteResponse::PACKET_RECEIVED:
            printf("Received packet!\n");
            break;
    }
    return true;
}

bool test_packet_tx_and_rx() {
    packet_receiver.reset();
    fail_received = false;
    const char* data = "This is a test\x18 of the emergency broadcast system.";
    size_t len = strlen(data);
    host_mcu_comms::transmit_packet(host_mcu_comms::kMsgTestPing,
                                    (const uint8_t*)data, len);
    if (fail_received) {
        printf("FAIL - failure result received during packet transmission\n");
        return false;
    } else if (!packet_receiver.valid()) {
        printf("FAIL - packet not received\n");
        return false;
    } else if (packet_receiver.packet_type() != host_mcu_comms::kMsgTestPing) {
        printf("FAIL - packet type not received correctly (%X, expected %X)\n",
               packet_receiver.packet_type(), host_mcu_comms::kMsgTestPing);
        return false;
    } else if (memcmp(buffer + 2, data, strlen(data))) {
        printf("FAIL - data not received correctly\n");
        return false;
    } else {
        printf("PASS - packet received\n");
    }
    return true;
}

int main() {
    // Simple packet round trip test.
    if (!test_packet_tx_and_rx()) return 1;
    return 0;
}
