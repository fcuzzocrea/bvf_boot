#!/usr/bin/env python
# encoding: utf-8
# Francescodario Cuzzocrea 2023

from waflib.Configure import conf


@conf
def find_fp6_openocd(conf):
    conf.find_program("openocd", var="OPENOCD", mandatory=False)
    conf.find_program("fpServer", mandatory=False)


def configure(conf):
    openocd_args = [
        ' --command "set DEVICE MPFS"',
        ' --command "set COREID 0"',
        ' --file /usr/share/openocd/scripts/board/microsemi-riscv.cfg',
    ]

    gdb_openocd_flags = [
          ' --batch'
          ' -ex "set arch riscv:rv64"'
          ' -ex "set mem inaccessible-by-default off"'
          ' -ex "target extended-remote localhost:3333"'
          ' -ex "monitor reset halt"'
          ' -ex "load"'
          ' -ex "monitor resume"'
          ' -ex "monitor shutdown"'
          ' -ex "quit"'
    ]

    # gdb_openocd_flags = [
    #     ' --batch',
    #     ' -ex "set mem inaccessible-by-default off"',
    #     ' -ex "set $riscv=1"',
    #     ' -ex "set arch riscv:rv64"',
    #     ' -ex "target extended-remote localhost:3333"',
    #     ' -ex "start"',
    #     ' -ex "load"',
    #     ' -ex "monitor resume"',
    #     ' -ex "monitor shutdown"',
    #     ' -ex "quit"',
    # ]

    conf.find_fp6_openocd()
    conf.env.OPENOCD_ARGS = openocd_args
    conf.env.GDB_OPENOCD_FLAGS = gdb_openocd_flags
