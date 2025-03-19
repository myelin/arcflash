// Based on https://github.com/stbrumme/crc32/blob/7a028136d54f8fe93b7cf533ca098f0bf30c3fbd/Crc32.cpp

// //////////////////////////////////////////////////////////
// Crc32.cpp
// Copyright (c) 2011-2019 Stephan Brumme. All rights reserved.
// Slicing-by-16 contributed by Bulat Ziganshin
// Tableless bytewise CRC contributed by Hagai Gold
// see http://create.stephan-brumme.com/disclaimer.html
//

#include "crc32.h"

/// compute CRC32 (half-byte algoritm)
uint32_t crc32(const void* data, size_t length, uint32_t previousCrc32)
{
  uint32_t crc = ~previousCrc32; // same as previousCrc32 ^ 0xFFFFFFFF
  const uint8_t* current = (const uint8_t*) data;

  /// look-up table for half-byte, same as crc32Lookup[0][16*i]
  static const uint32_t Crc32Lookup16[16] =
  {
    0x00000000,0x1DB71064,0x3B6E20C8,0x26D930AC,0x76DC4190,0x6B6B51F4,0x4DB26158,0x5005713C,
    0xEDB88320,0xF00F9344,0xD6D6A3E8,0xCB61B38C,0x9B64C2B0,0x86D3D2D4,0xA00AE278,0xBDBDF21C
  };

  while (length-- != 0)
  {
    crc = Crc32Lookup16[(crc ^  *current      ) & 0x0F] ^ (crc >> 4);
    crc = Crc32Lookup16[(crc ^ (*current >> 4)) & 0x0F] ^ (crc >> 4);
    current++;
  }

  return ~crc; // same as crc ^ 0xFFFFFFFF
}
