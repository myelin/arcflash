// Copyright 2019 Google LLC
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

#ifndef ARCFLASH
#error Makefile must define ARCFLASH
#endif

#include <stdint.h>
#include "arcregs.h"
#include "arcflash.pb.h"
#include "keyboard.h"


#define STB_SPRINTF_NOUNALIGNED
#define STB_SPRINTF_NOINT64
#define STB_SPRINTF_NOFLOAT
#include "../third_party/stb/stb_sprintf.h"

// main.cc
extern uint32_t _millis;
inline uint32_t millis() { return _millis; }

#define SERIAL_FRAMING_ERROR 0x100
#define SERIAL_TIMEOUT 0x200
extern uint32_t read_serial_byte();

// cmos.cc
extern void read_cmos();

// descriptor.cc
extern void parse_descriptor_and_print_menu(uint32_t rom_base, arcflash_FlashDescriptor* desc);

// display.cc
#define WIDTH 640
#define HEIGHT 256
#define WHITE 255
#define BLACK 0
#define SCREEN_ADDR(x, y) (SCREEN + (y) * WIDTH + (x))
#define SCREEN_END SCREEN_ADDR(WIDTH, HEIGHT)
extern int display_x, display_y;
extern void display_goto(int x, int y);
extern void display_print_char(char c);
extern void display_print(const char* s);
extern void display_print_hex(uint32_t v);
extern void display_printf(char const *format, ...);

// test.cc
extern void run_tests();
