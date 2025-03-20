// Copyright 2025 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// Communication protocol between the host and MCU.

#include "host_mcu_comms.h"

#include "crc32.h"

#ifdef TESTING
#include <stdio.h>
#define DEBUG_PRINTF printf
#else
#define DEBUG_PRINTF (void)
#endif

namespace host_mcu_comms {

namespace {

bool transmit_escaped_byte(uint8_t tx_byte) {
    if (tx_byte == 0x18) {
        if (!transmit_byte(0x18)) return false;
        return transmit_byte('X');
    }
    return transmit_byte(tx_byte);
}

};  // namespace

bool transmit_packet(int packet_type, const uint8_t *packet_data,
                     size_t packet_length) {
    // Send 0x18
    if (!transmit_byte(0x18)) return false;
    // Send 'P'
    if (!transmit_byte('P')) return false;
    // Send two-byte content type
    uint8_t packet_type_encoded[2] = {
        (uint8_t)((packet_type >> 8) & 0xFF),
        (uint8_t)(packet_type & 0xFF),
    };
    if (!transmit_byte(packet_type_encoded[0])) return false;
    if (!transmit_byte(packet_type_encoded[1])) return false;
    uint32_t crc = crc32(packet_type_encoded, 2);
    // Send packet data
    for (int i = 0; i < packet_length; ++i) {
        if (!transmit_escaped_byte(packet_data[i])) return false;
    }
    crc = crc32(packet_data, packet_length, crc);
    // Send four CRC32 bytes
    for (int i = 0; i < 4; ++i) {
        if (!transmit_byte((crc & 0xFF))) return false;
        crc >>= 8;
    }
    // Send 0x18
    if (!transmit_byte(0x18)) return false;
    // Send 'F'
    if (!transmit_byte('F')) return false;

    return true;
}

// Handle an incoming byte.
ProcessReceivedByteResponse PacketReceiver::process_received_byte(
    uint8_t rx_byte) {
    if (last_char_was_escape_) {
        last_char_was_escape_ = false;
        if (rx_byte == 'P') {
            // Start of packet.
            buffer_pos_ = 0;
            reading_packet_ = true;
            return ProcessReceivedByteResponse::OK;
        }
        if (rx_byte == 'F') {
            // End of packet.
            reading_packet_ = false;
            // Verify CRC32.
            if (buffer_pos_ < 4) {
                // Packet too short -- checksum missing?
                return fail();
            }
            uint32_t crc = crc32(buffer_, buffer_pos_);
            // Compare with CRC32 verify value
            // (https://en.wikipedia.org/wiki/Ethernet_frame#Frame_check_sequence).
            if (crc != 0x2144DF1C) {
                return fail();
            }
            // We have a packet!
            packet_received_ = true;
            return ProcessReceivedByteResponse::PACKET_RECEIVED;
        }
        if (rx_byte == 'X') {
            return add_byte_to_buffer(0x18);
        }
        // Invalid escape.
        return fail();
    }

    // Is it an escape char?
    if (rx_byte == 0x18) {
        last_char_was_escape_ = true;
        return ProcessReceivedByteResponse::OK;
    }

    // It's a normal char: add to buffer.
    return add_byte_to_buffer(rx_byte);
}

// Add a received byte to the buffer, if we have room.
ProcessReceivedByteResponse PacketReceiver::add_byte_to_buffer(
    uint8_t rx_byte) {
    // Check that we have room.
    if (buffer_pos_ >= buffer_size_) {
        return fail();
    }
    buffer_[buffer_pos_++] = rx_byte;
    return ProcessReceivedByteResponse::OK;
}

}  // namespace host_mcu_comms
