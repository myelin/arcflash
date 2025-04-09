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

// include sprintf implementation when arcflash pulls in stb_sprintf.h
#define STB_SPRINTF_IMPLEMENTATION

#include "arcflash.h"
#include <stdarg.h>

size_t strlen(const char* s) {
  size_t len = 0;
  while (*s++) ++len;
  return len;
}

void display_printf(char const *format, ...) {
  va_list ap;
  va_start(ap, format);
  char buf[500];
  int ret = stbsp_vsnprintf(buf, 500, format, ap);
  if (ret < 0) {
   display_print("printf error");
  } else {
   display_print(buf);
  }
  va_end(ap);
}
