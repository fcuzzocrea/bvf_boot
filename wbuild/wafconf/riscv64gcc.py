#!/usr/bin/env python
# encoding: utf-8
# Thomas Nagy, 2006-2018 (ita)
# Ralf Habacker, 2006 (rh)
# Yinon Ehrlich, 2009
# Francescodario Cuzzocrea 2023

"""
RISCV64 GCC detection.
"""

from waflib import Logs
from waflib.Configure import conf


@conf
def find_riscv64gcc(conf):
    """
    Find the program gcc, and if present, try to detect its version number
    """
    cc = conf.find_program('riscv64-unknown-elf-gcc', var='CC', mandatory=True)
    conf.find_program('riscv64-unknown-elf-gcc', var='AS', mandatory=True)
    conf.find_program('riscv64-unknown-elf-gcc-ar', var='AR', mandatory=True)
    conf.find_program('riscv64-unknown-elf-g++', var='CPP', mandatory=True)
    conf.find_program('riscv64-unknown-elf-ld', var='LD', mandatory=True)
    conf.find_program('riscv64-unknown-elf-objcopy', var='OBJCOPY', mandatory=True)
    conf.find_program('riscv64-unknown-elf-objdump', var='OBJDUMP', mandatory=True)
    conf.find_program('riscv64-unknown-elf-gcc-ranlib', var='RANLIB', mandatory=True)
    conf.find_program('riscv64-unknown-elf-strip', var='STRIP', mandatory=True)
    conf.find_program('riscv64-unknown-elf-size', var='SIZE', mandatory=True)
    conf.find_program('riscv64-unknown-elf-gcc', var='LINK_CC', mandatory=True)
    conf.find_program('riscv64-unknown-elf-gdb', var='GDB', mandatory=False)
    conf.get_cc_version(cc, gcc=True)
    conf.env.CC_NAME = 'riscv64gcc'


def configure(conf):
    """
    Configuration for gcc
    """
    libs = []
    c_flags = ['-mno-save-restore']

    conf.load('c_config')
    conf.find_riscv64gcc()
    conf.cc_add_flags()
    conf.link_add_flags()
    conf.load('asm')

    conf.env.CC_SRC_F = []
    conf.env.CC_TGT_F = ['-c', '-o']

    conf.env.AS_TGT_F = ['-c', '-o']
    conf.env.ASLNK_TGT_F = ['-o']

    conf.env.ARFLAGS = ['rcs']

    conf.env.CCLNK_SRC_F = []
    conf.env.CCLNK_TGT_F = ['-o']
    conf.env.CPPPATH_ST = '-I%s'
    conf.env.DEFINES_ST = '-D%s'

    conf.env.LIB_ST = '-l%s'  # template for adding libs
    conf.env.LIBPATH_ST = '-L%s'  # template for adding libpaths
    conf.env.STLIB_ST = '-l%s'
    conf.env.STLIBPATH_ST = '-L%s'

    conf.env.STLIB_MARKER = '-Wl,-Bstatic'

    conf.env.cprogram_PATTERN = '%s'

    conf.env.LINKFLAGS_cstlib = ['-Wl,-Bstatic']
    conf.env.cstlib_PATTERN = 'lib%s.a'

    conf.env.append_unique('CFLAGS', c_flags)
    conf.env.LIB = libs

