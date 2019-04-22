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


// Main C++ entrypoint.  By the time this is called, we know the memory is
// working, and everything necessary to execute C++ code has been done.

// All of this code will execute from RAM, because .text and .rodata are
// placed in the .data segment by switcher.ld, and are copied into RAM in
// start.s, right before branching to cstartup. This allows everything to run
// while the flash is inaccessible (i.e. when it's being updated, or when
// we're switching banks), and gives us a speed boost without having to
// configure the ROM access timing.

#include "arcflash.h"

#define BUF_SIZE 512
uint32_t buf[BUF_SIZE];

// Timer
uint32_t _millis = 0;

// mouse position on screen
int mouse_x = WIDTH / 2, mouse_y = HEIGHT / 2;

// Decoded descriptor proto, from flash
arcflash_FlashDescriptor descriptor;

// disable interrupts by setting bits 26 (F) and 27 (I) in the PSR
void disable_interrupts() {
  asm volatile (
    "mov r0, pc\n\t"
    "orr r0, r0, #0xc000000\n\t"  // (1<<26) | (1<<27)
    "teqp r0, #0\n\t"
    ::: "r0"
  );
}

// enable interrupts by clearing bits 26 (F) and 27 (I) in the PSR
void enable_interrupts() {
  asm volatile (
    "mov r0, pc\n\t"
    "and r0, r0, #0xf3ffffff\n\t"  // ((1<<26) | (1<<27)) ^ 0xffffffff
    "teqp r0, #0\n\t"
    ::: "r0"
  );
}

#define UART_HALF_BIT_TIME true
#define UART_FULL_BIT_TIME false
static void setup_bitbang_uart(bool half_time) {
  // Set IOC timer period to support bit-banged UART operation.

  // IOC timer 0 and 1 clock at RCLK/4, i.e. 2MHz on an A3000.  According to
  // steve3000 on Stardot, IOC is always clocked at 8MHz on Archimedes
  // machines, so we can use IOC timers to set a consistent bit rate.

#define UART_BAUD 57500
  uint32_t uart_timer = 2000000L / UART_BAUD;
  // half_time is used when reading the start bit
  if (half_time == UART_HALF_BIT_TIME) uart_timer >>= 1;

  SETUP_IOC_TIMER1(uart_timer);
}

void write_serial_tx(int b) {
  volatile uint32_t *ptr = (volatile uint32_t *)(0x3fffff0L + ((b & 1) ? 4 : 0));
  // force compiler to read *ptr even though we don't care about the result
  asm volatile ("" : "=m" (*ptr) : "r" (*ptr));
}

int read_serial_rx() {
  return (*(volatile uint32_t *)0x3fffff8L) & 1;
}

void write_serial_byte(uint8_t c) {
  volatile uint32_t *zero = (volatile uint32_t *)0x3fffff0L;
  volatile uint32_t *one = (volatile uint32_t *)0x3fffff4L;

  // Timer 1 underflow will set TM1 in IOC_IRQ_STATUS_A, so we can synchronize
  // our bit timings to that.

  setup_bitbang_uart(UART_FULL_BIT_TIME);
  (void)*one;
  uint32_t data = ((c & 0xff) | 0xf00) << 1;
  IOC_CLEAR_TM1();
  for (uint32_t i = 0; i < 11; ++i) {
    while (!IOC_TM1);
    IOC_CLEAR_TM1();
    if (data & 1) {
      (void)*one;
    } else {
      (void)*zero;
    }
    data >>= 1;
  }

  // Sadly, all this hand-coded assembly isn't nearly as good as what GCC
  // produces with -O2!  Keeping it here for posterity.

  // asm volatile (
  //   "ldr r0, [%[one]]\n\t"  // make sure TX is high to begin with
  //   "str %[ioc_irq_clear_tm1], [%[ioc_irq_clear]]\n\t"  // clear previous TM1 interrupt
  //   // loop over 10 bits; r1 = loop counter
  //   "mov r1, #0\n\t"
  //   "serial_tx_loop:\n\t"
  //   // sync with timer
  //   "  serial_bit_wait:\n\t"
  //   "    ldr r0, [%[ioc_irq_status_a]]\n\t"
  //   "    ands r0, r0, %[ioc_irq_status_a_tm1]\n\t"
  //   "    beq serial_bit_wait\n\t"
  //   "   str %[ioc_irq_clear_tm1], [%[ioc_irq_clear]]\n\t"
  //   // send zero or one depending on %[data] LSB
  //   "  ands r0, %[data], #1\n\t"
  //   "  ldreq r0, [%[zero]]\n\t"
  //   "  ldrne r0, [%[one]]\n\t"
  //   // next bit
  //   "  lsr %[data], %[data], #1\n\t"
  //   "  add r1, r1, #1\n\t"
  //   "  cmp r1, #11\n\t"
  //   "  blo serial_tx_loop\n\t"
  //   : // outputs
  //   : // inputs
  //     [zero] "r" (zero),
  //     [one] "r" (one),
  //     [data] "r" (((c & 0xff) | 0xf00) << 1),  // {11111111, data[7:0], 0} = stop bit and buffer, data byte, start bit
  //     [ioc_irq_clear] "r" (&IOC_IRQ_CLEAR),
  //     [ioc_irq_status_a] "r" (&IOC_IRQ_STATUS_A),
  //     [ioc_irq_status_a_tm1] "r" (IOC_IRQ_STATUS_A_TM1),
  //     [ioc_irq_clear_tm1] "r" (IOC_IRQ_CLEAR_TM1)
  //   : // clobbers
  //     "r0",
  //     "r1"
  //   );
}

// Returns:
// - a byte read from the serial port,
// - or 0x100 for a framing error,
#define SERIAL_FRAMING_ERROR 0x100
// - or 0x200 for a timeout
#define SERIAL_TIMEOUT 0x200
uint32_t read_serial_byte() {
  volatile uint32_t *rxd = (volatile uint32_t *)0x3fffff8L;
#define RXD ((*rxd) & 1)
  // This is a bit trickier than writing a byte, because we want to sample in
  // the middle of the bits.  We can mess with TM1 to make this work though.

  // Set the timer up to time halfway through the start bit
  setup_bitbang_uart(UART_HALF_BIT_TIME);
  IOC_TIMER1_GO = 0;
  IOC_CLEAR_TM1();

  // Wait for the RXD falling edge
#define SERIAL_TIMEOUT_MILLIS 1000
  uint32_t timeout = SERIAL_TIMEOUT_MILLIS * (UART_BAUD * 2) / 1000;  // Number of TM1 underflows in 1 second
  while (RXD) {
    // Test for timeout
    if (IOC_TM1) {
      IOC_CLEAR_TM1();
      if (--timeout == 0) {
        return SERIAL_TIMEOUT;
      }
    }
  }

  // Reset timer and clear interrupt
  IOC_TIMER1_GO = 0;
  IOC_CLEAR_TM1();

  // Wait for timer underflow
  while (!IOC_TM1);
  IOC_CLEAR_TM1();

  // Reset timer to full bit time
  setup_bitbang_uart(UART_FULL_BIT_TIME);

  // Next timeout will be the middle of bit 0.  Read 9 bits, verify that the
  // last is a 1, then we have a byte.

  uint32_t data = 0;

  for (uint32_t i = 0; i < 9; ++i) {
    while (!IOC_TM1);
    IOC_CLEAR_TM1();
    data = (data >> 1) | (RXD << 8);
  }

  if (!(data & 0x100)) {
    // framing error
    return SERIAL_FRAMING_ERROR;
  }

  return data & 0xFF;
}

void timer_poll() {
    if (IOC_TM0) {
      IOC_CLEAR_TM0();
      _millis++;
    }
}

void delay(int ms) {
  uint32_t start = millis();
  while ((millis() - start) < ms) {
    timer_poll();
  }
}

void loop() {
  volatile uint8_t *pixptr = SCREEN_END;
  uint8_t debug_byte = 32;
  uint8_t white = 128;

  setup_bitbang_uart(UART_FULL_BIT_TIME);
  IOC_TIMER1_GO = 0;

  while (1) {
    timer_poll();
    keyboard_poll();

    int b = read_serial_rx();
    // write_serial_tx(b);  // DEBUG disabled this so i can see the write_serial_byte output (and tweak the NOPs to work at 8MHz)
    // output to screen
    if (pixptr >= SCREEN_ADDR(0, 248)) {
      pixptr = SCREEN_ADDR(0, 240);
      ++white;
      if (debug_byte != '*') write_serial_byte(debug_byte);
      ++debug_byte;
      if (debug_byte > 126) debug_byte = 32;
    }
    *pixptr++ = b ? white : BLACK;  // serial input status
    // int tm1_active = IOC_TM1 ? 1 : 0;
    // if (tm1_active) IOC_CLEAR_TM1();
    // *pixptr++ = tm1_active ? white : BLACK;  // TM1 interrupt status
  }
}

void keyboard_keydown(uint8_t keycode) {
  char c = 0;
  switch (keycode) {
    case KEY_1: c = '1'; break;
    case KEY_2: c = '2'; break;
    case KEY_3: c = '3'; break;
    case KEY_4: c = '4'; break;
    case KEY_5: c = '5'; break;
    case KEY_6: c = '6'; break;
    case KEY_7: c = '7'; break;
    case KEY_8: c = '8'; break;
    case KEY_9: c = '9'; break;
    case KEY_0: c = '0'; break;
    case KEY_A: c = 'A'; break;
    case KEY_B: c = 'B'; break;
    case KEY_C: c = 'C'; break;
    case KEY_D: c = 'D'; break;
    case KEY_E: c = 'E'; break;
    case KEY_F: c = 'F'; break;
    case KEY_G: c = 'G'; break;
    case KEY_H: c = 'H'; break;
    case KEY_I: c = 'I'; break;
    case KEY_J: c = 'J'; break;
    case KEY_K: c = 'K'; break;
    case KEY_L: c = 'L'; break;
    case KEY_M: c = 'M'; break;
    case KEY_N: c = 'N'; break;
    case KEY_O: c = 'O'; break;
    case KEY_P: c = 'P'; break;
    case KEY_Q: c = 'Q'; break;
    case KEY_R: c = 'R'; break;
    case KEY_S: c = 'S'; break;
    case KEY_T: c = 'T'; break;
    case KEY_U: c = 'U'; break;
    case KEY_V: c = 'V'; break;
    case KEY_W: c = 'W'; break;
    case KEY_X: c = 'X'; break;
    case KEY_Y: c = 'Y'; break;
    case KEY_Z: c = 'Z'; break;
  }

  if (c && c >= 'A' && c < 'A' + descriptor.bank_count) {
    // TODO turn this into a proper keyboard handler, but for now assume a
    // keydown on A-Z is to select an OS to boot

    int bank_id = c - 'A';
    arcflash_FlashBank* bank = &descriptor.bank[bank_id];

    display_goto(48, 216);
    display_printf("Selected OS %c (%s)", c, bank->bank_name);

    // This is the lower 7 bits of the byte that rom_emulator.ino sends to the
    // CPLD to select the flash bank.  As such, this msut stay in sync with
    // a3000_rom_emulator.v -- if we switch to 512k banks, the format will
    // change.
    uint8_t flash_bank_select_command =
      // 0x30 for 4M, 0x10 for 2M, 0 for 1M
      (bank->bank_size > 2*1048576 ? 0x30 :
        (bank->bank_size > 1048576 ? 0x10 : 0)) |
      // 0-15 in 1MB increments
      (bank->bank_ptr / 1048576);

    // Keep sending it to the MCU
    while (1) {
      write_serial_byte('*');
      write_serial_byte(flash_bank_select_command);
      delay(500);
    }
  }
}

void keyboard_keyup(uint8_t keycode) {
  // ignore
}

void keyboard_mousemove(int mouse_dx, int mouse_dy) {
  mouse_x += mouse_dx;
  mouse_y -= mouse_dy;
  if (mouse_x < 0) mouse_x = 0;
  if (mouse_x >= WIDTH) mouse_x = WIDTH - 1;
  if (mouse_y < 0) mouse_y = 0;
  if (mouse_y >= HEIGHT) mouse_y = HEIGHT - 1;
  *SCREEN_ADDR(mouse_x, mouse_y) = WHITE;
}

extern "C" void main_program() {
  // set border color: 40:8 X:11 supreme:1 blue:4 green:4 red:4
  // VIDCR = 0x40001FFFL;  // white
  // VIDCR = 0x40000F00L;  // blue
  VIDCR = 0x40000777L;  // grey

  // Set up IOC timer0 to tick at 1 kHz (1 ms)
  SETUP_IOC_TIMER0(IOC_TICKS_PER_US * 1000);
  IOC_TIMER0_GO = 0;

  // Initialize serial output
  write_serial_byte(0);

  // Initialize keyboard (IOC timer3 etc)
  keyboard_init();

  // Draw horizontal (rainbow) bars on screen
  uint8_t c = 0;
  for (uint32_t y = 24; y < 32; ++y) {
    for (uint32_t x = 0; x < WIDTH; ++x) {
      SCREEN[y * WIDTH + x] = c++;
    }
  }
  for (uint32_t y = 232; y < 240; ++y) {
    for (uint32_t x = 0; x < WIDTH; ++x) {
      SCREEN[y * WIDTH + x] = c++;
    }
  }

  display_goto(0, 40);

  read_cmos();

  parse_descriptor_and_print_menu(ARC_ROM_BASE, &descriptor);

  // TODO init IOC and check keyboard

  // Bit-banged serial port
  // DEBUG: just echo RXD (cpld_MOSI, 0x3fffff8) back to TXD (cpld_MISO, 0x3fffff0 + (bit ? 4 : 0))
  // if (0) {
  //   volatile uint8_t *pixptr = SCREEN_END;
  //   volatile uint8_t *screen_mid = SCREEN_ADDR(0, HEIGHT/2), *screen_end = SCREEN_END;
  //   uint32_t readaddr = 0x3fffff8L, sendone = 0x3fffff4L, sendzero = 0x3fffff0L, black = 0, white = 136;  // 256=white 136=blue 21=red
  //   asm volatile(
  //     "next:\n\t"
  //     "  cmp %[pixptr], %[screen_end]\n\t"
  //     "  movhi %[pixptr], %[screen_mid]\n\t"
  //     "  ldr r0, [%[readaddr]]\n\t"
  //     "  tst r0, #1\n\t"
  //     "  beq one\n\t"
  //     "  ldr r1, [%[sendone]]\n\t"
  //     "  strb %[white], [%[pixptr]]\n\t"
  //     "  add %[pixptr], %[pixptr], #1\n\t"
  //     "  b next\n\t"
  //     "one:\n\t"
  //     "  ldr r1, [%[sendzero]]\n\t"
  //     "  strb %[black], [%[pixptr]]\n\t"
  //     "  add %[pixptr], %[pixptr], #1\n\t"
  //     "  b next\n\t"
  //     : [pixptr] "+r" (pixptr)
  //     : [readaddr] "r" (readaddr),
  //       [sendone] "r" (sendone),
  //       [sendzero] "r" (sendzero),
  //       [screen_end] "r" (screen_end),
  //       [screen_mid] "r" (screen_mid),
  //       [black] "r" (black),
  //       [white] "r" (white)
  //     : "r0", "r1");
  // }
  loop();
}
