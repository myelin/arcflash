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

#ifndef __HOST_MCU_COMMS_H
#define __HOST_MCU_COMMS_H

#include <stddef.h>
#include <stdint.h>

namespace host_mcu_comms {

// Bit rate for UART comms.
// Host->MCU comms works 100% at 25000, fails 100% at 50000.
// -- although the MCU sometimes just completely misses an
// entire packet once in a while even at very slow rates.
// MCU->host comms works 100% at 17000, 5% of the time at 20000.
// Use 10k for safety.
inline constexpr uint32_t kUartBaud = 10000;

// Message types.
#define DEFINE_MESSAGE_TYPE(name, a, b) \
    inline constexpr int name = ((a) << 8 | (b))
DEFINE_MESSAGE_TYPE(kMsgSelectRom, 'S', 'R');
DEFINE_MESSAGE_TYPE(kMsgTestPing, 'T', 'P');
DEFINE_MESSAGE_TYPE(kMsgTestResponse, 'T', 'R');

// host_mcu_comms::transmit_byte: transmit a byte over the serial channel.
//
// Returns true on success, false on failure.
//
// This must be implemented by the caller.

extern bool transmit_byte(uint8_t tx_byte);

// host_mcu_comms::transmit_packet: Transmit an entire packet.
//
// Returns true on success, false on failure.

extern bool transmit_packet(int packet_type, const uint8_t* packet_data,
                            size_t packet_length);

enum class ProcessReceivedByteResponse {
    OK,
    FAIL,
    PACKET_RECEIVED,
};

class PacketReceiver {
   public:
    PacketReceiver(uint8_t* buffer, size_t buffer_size)
        : buffer_(buffer), buffer_size_(buffer_size) {}

    // Handle a byte received from the serial channel.
    //
    // On the MCU, this is called whenever a byte shows up on the serial
    // channel, and return codes other than PACKET_RECEIVED are ignored.
    //
    // On the host, this is called during a blocking "receive packet"
    // operation, which will abort if a FAIL return code is received.
    ProcessReceivedByteResponse process_received_byte(uint8_t rx_byte);

    // Return true if we have received a packet with a valid checksum.
    bool valid() { return packet_received_; }

    // Return packet type.
    int packet_type() { return buffer_[1] | (buffer_[0] << 8); }

    // Return pointer to start of message.
    const uint8_t *message() { return buffer_ + 2; }

    // Return size of received packet.
    size_t size() { return buffer_pos_ - 6; }

    // Reset to idle state, so we can receive another packet.
    void reset() {
        buffer_pos_ = 0;
        last_char_was_escape_ = false;
        reading_packet_ = false;
        packet_received_ = false;
    }

   private:
    // Helper method so process_received_byte etc. can just return fail().
    ProcessReceivedByteResponse fail() {
        reset();
        return ProcessReceivedByteResponse::FAIL;
    }

    // Store a byte in the buffer.
    ProcessReceivedByteResponse add_byte_to_buffer(uint8_t rx_byte);

    // Data buffer pointer.
    uint8_t* buffer_ = nullptr;
    // Data buffer size.
    size_t buffer_size_ = 0;
    // Current position in receive buffer.
    size_t buffer_pos_ = 0;
    // Last received char was 0x18.
    bool last_char_was_escape_ = false;
    // Reading packet body (between 0x18 P and 0x18 F)
    bool reading_packet_ = false;
    // Flag set when packet is fully received.
    bool packet_received_ = false;
};

}  // namespace host_mcu_comms

#endif  // __HOST_MCU_COMMS_H
