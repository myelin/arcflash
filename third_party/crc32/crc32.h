// Based on https://github.com/stbrumme/crc32/blob/7a028136d54f8fe93b7cf533ca098f0bf30c3fbd/Crc32.h

#ifndef __CRC32_H
#define __CRC32_H

// //////////////////////////////////////////////////////////
// Crc32.h
// Copyright (c) 2011-2019 Stephan Brumme. All rights reserved.
// Slicing-by-16 contributed by Bulat Ziganshin
// Tableless bytewise CRC contributed by Hagai Gold
// see http://create.stephan-brumme.com/disclaimer.html
//

// uint8_t, uint32_t, int32_t
#include <stdint.h>
// size_t
#include <stddef.h>

/// compute CRC32 (half-byte algoritm)
uint32_t crc32(const void* data, size_t length, uint32_t previousCrc32 = 0);

#endif  // __CRC32_H
