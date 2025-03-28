// Based on third_party/bossa/bossac.cpp.
// Modifications by Phillip Pearson to turn it into a Python extension module.

///////////////////////////////////////////////////////////////////////////////
// BOSSA
//
// Copyright (c) 2011-2018, ShumaTech
// All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are met:
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//     * Neither the name of the <organization> nor the
//       names of its contributors may be used to endorse or promote products
//       derived from this software without specific prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
// ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
// WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
// DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
// DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
// (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
// LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
// ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
// (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
// SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
///////////////////////////////////////////////////////////////////////////////

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <string>
#include <exception>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>

#include <chrono>
#include <thread>

#include "Samba.h"
#include "PortFactory.h"
#include "Device.h"
#include "Flasher.h"

using namespace std;

struct BossaConfig
{
    string portPath;
    bool erase;
    bool write;
    bool read;
    bool verify;
    int offset;
    bool reset;
    bool boot;
    int bootArg;
    bool info;
    bool debug;
    bool arduinoReset;
};

class BossaObserver : public FlasherObserver
{
public:
    BossaObserver() : _lastTicks(-1) {}
    virtual ~BossaObserver() {}

    virtual void onStatus(const char *message, ...);
    virtual void onProgress(int num, int div);
private:
    int _lastTicks;
};

void
BossaObserver::onStatus(const char *message, ...)
{
    va_list ap;

    va_start(ap, message);
    vprintf(message, ap);
    va_end(ap);
}

void
BossaObserver::onProgress(int num, int div)
{
    int ticks;
    int bars = 30;

    ticks = num * bars / div;

    if (ticks == _lastTicks)
        return;

    printf("\r[");
    while (ticks-- > 0)
    {
        putchar('=');
        bars--;
    }
    while (bars-- > 0)
    {
        putchar(' ');
    }
    printf("] %d%% (%d/%d pages)", num * 100 / div, num, div);
    fflush(stdout);

    _lastTicks = 0;
}

static std::chrono::time_point<std::chrono::steady_clock> start_time;

void
timer_start()
{
    start_time = std::chrono::steady_clock::now();
}

float
timer_stop()
{
    auto end = std::chrono::steady_clock::now();
    float microseconds = (float)std::chrono::duration_cast<std::chrono::microseconds>(end - start_time).count();
    return microseconds / 1000000.0;
}

int
program_device(const char* port, const char* filename)
{
    // Replicate what arduino-cli does:
    //
    // bossac -i -d --port=cu.usbmodem1101 -U --offset=0x2000 -w -v "./firmware.ino.bin" -R

    BossaConfig config = {
        .portPath = port,
        .erase = false,
        .write = true,
        .read = false,
        .verify = true,
        .offset = 0x2000,
        .reset = true,
        .boot = false,
        .bootArg = 0,
        .info = true,
        .debug = true,
        .arduinoReset = true,
    };

    try
    {
        Samba samba;
        PortFactory portFactory;

        if (config.debug)
            samba.setDebug(true);

        if (config.arduinoReset)
        {
            SerialPort::Ptr port;
            port = portFactory.create(config.portPath, true);

            printf("Arduino 1200 baud reset\n");
            if(!port->open(1200))
            {
                fprintf(stderr, "Failed to open port at 1200bps\n");
                return 1;
            }

            port->setRTS(true);
            port->setDTR(false);
            port->close();

            // wait for chip to reboot and USB port to re-appear
            std::this_thread::sleep_for(std::chrono::seconds(1));

            if (config.debug)
                printf("Arduino reset done\n");
        }

        if (config.portPath.empty())
        {
            fprintf(stderr, "No serial ports available\n");
            return 1;
        }

        if (!samba.connect(portFactory.create(config.portPath, true)))
        {
            fprintf(stderr, "No device found on %s\n", config.portPath.c_str());
            return 1;
        }

        Device device(samba);
        device.create();

        Device::FlashPtr& flash = device.getFlash();

        BossaObserver observer;
        Flasher flasher(samba, device, observer);

        if (config.info)
        {
            FlasherInfo info;
            flasher.info(info);
            info.print();
        }

        if (config.erase)
        {
            timer_start();
            flasher.erase(config.offset);
            printf("\nDone in %5.3f seconds\n", timer_stop());
        }

        if (config.write)
        {
            timer_start();
            flasher.write(filename, config.offset);
            printf("\nDone in %5.3f seconds\n", timer_stop());
        }

        if (config.verify)
        {
            uint32_t pageErrors;
            uint32_t totalErrors;

            timer_start();
            if (!flasher.verify(filename, pageErrors, totalErrors, config.offset))
            {
                printf("\nVerify failed\nPage errors: %d\nByte errors: %d\n",
                    pageErrors, totalErrors);
                return 2;
            }

            printf("\nVerify successful\nDone in %5.3f seconds\n", timer_stop());
        }

        if (config.read)
        {
            timer_start();
            flasher.read(filename, 0, config.offset);
            printf("\nDone in %5.3f seconds\n", timer_stop());
        }

        if (config.boot)
        {
            printf("Set boot flash %s\n", config.bootArg ? "true" : "false");
            flash->setBootFlash(config.bootArg);
        }

        flash->writeOptions();

        if (config.reset)
            device.reset();
    }
    catch (exception& e)
    {
        fprintf(stderr, "\n%s\n", e.what());
        return 1;
    }
    catch(...)
    {
        fprintf(stderr, "\nUnhandled exception\n");
        return 1;
    }

    return 0;
}


static PyObject *
_bossa_program(PyObject *self, PyObject *args)
{
    const char* port;
    const char* filename;

    if (!PyArg_ParseTuple(args, "ss", &port, &filename))
        return NULL;
    int result = program_device(port, filename);
    return PyLong_FromLong(result);
}

static PyMethodDef BossaMethods[] = {
    {"program", _bossa_program, METH_VARARGS,
     "Program a microcontroller with BOSSA."},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

static struct PyModuleDef _bossamodule = {
    PyModuleDef_HEAD_INIT,
    "_bossa",   /* name of module */
    NULL, /* module documentation, may be NULL */
    -1,       /* size of per-interpreter state of the module,
                 or -1 if the module keeps state in global variables. */
    BossaMethods
};

PyMODINIT_FUNC
PyInit__bossa(void)
{
    PyObject *m;

    m = PyModule_Create(&_bossamodule);
    if (m == NULL)
        return NULL;

    return m;
}
