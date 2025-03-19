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

// host_mcu_comms::transmit_byte: transmit a byte over the serial channel.
//
// Returns true on success, false on failure.
//
// This must be implemented by the caller.

extern bool transmit_byte(uint8_t tx_byte);

// host_mcu_comms::transmit_packet: Transmit an entire packet.
//
// Returns true on success, false on failure.

extern bool transmit_packet(const uint8_t* packet_data, size_t packet_length);

// host_mcu_comms::process_received_byte: handle a byte received from the serial
// channel.
//
// On the MCU, this is called whenever a byte shows up on the serial
// channel, and return codes other than PACKET_RECEIVED are ignored.
//
// On the host, this is called during a blocking "receive packet"
// operation, which will abort if a FAIL return code is received.

enum class ProcessReceivedByteResponse {
  OK,
  FAIL,
  PACKET_RECEIVED,
};

extern ProcessReceivedByteResponse process_received_byte(uint8_t rx_byte);

}  // namespace host_mcu_comms

#endif  // __HOST_MCU_COMMS_H
