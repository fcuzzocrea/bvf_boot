#!/usr/bin/env python
# encoding: utf-8
# Thomas Nagy, 2006-2018 (ita)
# Ralf Habacker, 2006 (rh)
# Yinon Ehrlich, 2009
# Francescodario Cuzzocrea 2024

"""
RISCV64 GCC detection.
"""

import os

from waflib.Configure import conf


@conf
def find_riscv64gcc(conf):
    """
    Find the program gcc, and if present, try to detect its version number
    """
    cc = conf.find_program('riscv-rtems6-gcc', var='CC', mandatory=True)
    conf.find_program('riscv-rtems6-gcc', var='AS', mandatory=True)
    conf.find_program('riscv-rtems6-gcc-ar', var='AR', mandatory=True)
    conf.find_program('riscv-rtems6-cpp', var='CPP', mandatory=True)
    conf.find_program('riscv-rtems6-ld', var='LD', mandatory=True)
    conf.find_program('riscv-rtems6-objcopy', var='OBJCOPY', mandatory=True)
    conf.find_program('riscv-rtems6-objdump', var='OBJDUMP', mandatory=True)
    conf.find_program('riscv-rtems6-gcc-ranlib', var='RANLIB', mandatory=True)
    conf.find_program('riscv-rtems6-strip', var='STRIP', mandatory=True)
    conf.find_program('riscv-rtems6-size', var='SIZE', mandatory=True)
    conf.find_program('riscv-rtems6-gcc', var='LINK_CC', mandatory=True)
    conf.find_program('riscv-rtems6-gdb', var='GDB', mandatory=False)
    conf.find_program('riscv-rtems6-gcov', var='GCOV', mandatory=False)
    conf.get_cc_version(cc, gcc=True)
    conf.env.CC_NAME = 'riscvrtems6'


def configure(conf):
    """
    Configuration for gcc
    """
    libs = []

    c_flags = ['-isystem' + os.path.join(os.environ['RTEMSBSPROOT'],
               conf.env.ARCH.replace('rv', 'mpfs'), 'lib', 'include')]

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
