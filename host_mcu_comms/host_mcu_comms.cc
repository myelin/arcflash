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

namespace host_mcu_comms {

bool transmit_packet(const uint8_t packet_type[2], const uint8_t *packet_data,
                     size_t packet_length) {
  return true;
}

ProcessReceivedByteResponse process_received_byte(uint8_t rx_byte) {
  return ProcessReceivedByteResponse::OK;
}

}  // namespace host_mcu_comms
