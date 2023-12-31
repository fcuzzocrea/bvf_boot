#!/usr/bin/env python
# encoding: utf-8
# Thomas Nagy, 2006-2018 (ita)
# Francescodario Cuzzocrea, 2023

# This a slight modification of the original source: waflib/Tools/c.py;
# do not use absolute paths in the "run_str" variable.

"Base for c programs/libraries"

from waflib import TaskGen, Task
from waflib.Tools import c_preproc
from waflib.Tools.ccroot import link_task, stlink_task
from waflib.Utils import def_attrs
from waflib.TaskGen import feature, after_method


@TaskGen.extension('.c')
def c_hook(self, node):
    "Binds the c file extensions create :py:class:`waflib.Tools.c.c` instances"
    if not self.env.CC and self.env.CXX:
        return self.create_compiled_task('cxx', node)
    return self.create_compiled_task('c', node)


class c(Task.Task):
    "Compiles C files into object files"
    run_str = '${CC} ${ARCH_ST:ARCH} ${CFLAGS} ${FRAMEWORKPATH_ST:FRAMEWORKPATH} ${CPPPATH_ST:INCPATHS} ${DEFINES_ST:DEFINES} ${CC_SRC_F}${SRC} ${CC_TGT_F}${TGT[0].abspath()} ${CPPFLAGS}'
    vars = ['CCDEPS']  # unused variable to depend on, just in case
    ext_in = ['.h']  # set the build order easily by using ext_out=['.h']
    scan = c_preproc.scan


class cprogram(link_task):
    "Links object files into c programs"
    run_str = '${LINK_CC} ${LINKFLAGS} ${CCLNK_SRC_F}${SRC} ${CCLNK_TGT_F}${TGT[0].abspath()} ${RPATH_ST:RPATH} ${FRAMEWORKPATH_ST:FRAMEWORKPATH} ${FRAMEWORK_ST:FRAMEWORK} ${ARCH_ST:ARCH} ${STLIB_MARKER} ${STLIBPATH_ST:STLIBPATH} ${STLIB_ST:STLIB} ${SHLIB_MARKER} ${LIBPATH_ST:LIBPATH} ${LIB_ST:LIB} ${LDFLAGS}'
    ext_out = ['.bin']
    vars = ['LINKDEPS']
    inst_to = '${BINDIR}'


class cshlib(cprogram):
    "Links object files into c shared libraries"
    inst_to = '${LIBDIR}'


class cstlib(stlink_task):
    "Links object files into a c static libraries"
    pass  # do not remove


class strip(Task.Task):
    run_str = '${STRIP} -s ${SRC} -o ${TGT}'
    color = 'CYAN'


@feature('strip')
@after_method('apply_link')
def map_strip(self):
    def_attrs(self, strip_target=None)

    link_output = self.link_task.outputs[0]
    if not self.strip_target:
        self.strip_target = link_output.change_ext('.strip').name
    self.create_task('strip', src=link_output, tgt=self.path.find_or_declare(self.strip_target))


class disassemble(Task.Task):
    run_str = '${OBJDUMP} -S --disassemble ${SRC} > ${TGT}'
    color = 'PINK'


@feature('disassemble')
@after_method('apply_link')
def map_disassemble(self):
    def_attrs(self, disassemble_target=None)

    link_output = self.link_task.outputs[0]
    if not self.disassemble_target:
        self.disassemble_target = link_output.change_ext('.dis').name
    self.create_task('disassemble', src=link_output, tgt=self.path.find_or_declare(self.disassemble_target))


class bin(Task.Task):
    run_str = '${OBJCOPY} -O binary ${SRC} ${TGT}'
    color = 'CYAN'


@feature('bin')
@after_method('apply_link')
def map_bin(self):
    def_attrs(self, bin_target=None)

    link_output = self.link_task.outputs[0]
    if not self.bin_target:
        self.bin_target = link_output.change_ext('.bin').name
    self.create_task('bin', src=link_output, tgt=self.path.find_or_declare(self.bin_target))



class bin(Task.Task):
    run_str = '${OBJCOPY} -O binary ${SRC} ${TGT}'
    color = 'CYAN'


@feature('bin')
@after_method('apply_link')
def map_bin(self):
    def_attrs(self, bin_target=None)

    link_output = self.link_task.outputs[0]
    if not self.bin_target:
        self.bin_target = link_output.change_ext('.bin').name
    self.create_task('bin', src=link_output, tgt=self.path.find_or_declare(self.bin_target))


class hex(Task.Task):
    run_str = '${OBJCOPY} -O ihex ${HEX_OPTIONS} ${SRC} ${TGT}'
    color = 'CYAN'


@feature('hex')
@after_method('apply_link')
def map_hex(self):
    def_attrs(self, hex_target=None, hex_options='')

    link_output = self.link_task.outputs[0]
    if not self.hex_target:
        self.hex_target = link_output.change_ext('.ihex').name
    task = self.create_task('hex', src=link_output, tgt=self.path.find_or_declare(self.hex_target))

    try:
        task.env.append_unique('HEX_OPTIONS', getattr(self, 'objcopy_flags'))
    except AttributeError:
        pass
