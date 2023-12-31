#!/usr/bin/env python
# encoding: utf-8
# Francescodario Cuzzocrea 2023

from waflib import Logs
from waflib.Configure import conf

common_flags = [
    # Generate proper debug symbols for GDB and TRACE32
    '-ggdb3',
    '-gdwarf-2',

    # Place each function or data in a separate section, so the linker can discard unused ones
    '-fdata-sections',
    '-ffunction-sections',

    # Common flags
    '-fmessage-length=0',
    '-fsigned-char',
    '-msmall-data-limit=8',
    '-mstrict-align',
    '-fdiagnostics-color',
]

wall_flags = [
    # This section contains the warnings usually coming from  '-Wall',
    '-Waddress',
    '-Warray-bounds=1',
    '-Wbool-compare',
    '-Wbool-operation',
    '-Wchar-subscripts',
    '-Wcomment',
    '-Wenum-compare',
    '-Wformat',
    '-Wint-in-bool-context',
    '-Winit-self',
    '-Wlogical-not-parentheses',
    '-Wmaybe-uninitialized',
    '-Wmemset-elt-size',
    '-Wmemset-transposed-args',
    '-Wmisleading-indentation',
    '-Wno-attributes',
    '-Wmissing-braces',
    '-Wnarrowing',
    '-Wnonnull',
    '-Wnonnull-compare',
    '-Wopenmp-simd',
    '-Wparentheses',
    '-Wrestrict',
    '-Wreturn-type',
    '-Wsequence-point',
    '-Wsizeof-pointer-memaccess',
    '-Wstrict-aliasing',
    '-Wstrict-overflow=1',
    '-Wswitch',
    '-Wtautological-compare',
    '-Wtrigraphs',
    '-Wuninitialized',
    '-Wunused-label',
    '-Wunused-value',
    '-Wunused-variable',
    '-Wvolatile-register-var',
]

wextra_flags = [
    # This section contains the warnings usually coming from -Wextra
    '-Wclobbered',
    '-Wempty-body',
    '-Wignored-qualifiers',
    '-Wimplicit-fallthrough=3',
    '-Wmissing-field-initializers',
    '-Wtype-limits',
    '-Wuninitialized',
    '-Wshift-negative-value',
    '-Wunused-parameter',
    '-Wunused-but-set-parameter',
]

pedantic_flags = [
    # Other warnings
    # useful because usually testing floating-point numbers for equality is bad.
    '-Wfloat-equal',
    # warn whenever a local variable shadows another local variable,
    # parameter or global variable or whenever a built-in function is shadowed.
    '-Wshadow',
    # warn if anything depends upon the size of a function or of void.
    '-Wpointer-arith',
    # warns about cases where the compiler optimizes based on the assumption
    # that signed overflow does not occur. (The value 5 may be too strict, see the manual page.)
    '-Wstrict-overflow=5',
    # give string constants the type const char[length] so that copying
    # the address of one into a non-const char * pointer will get a warning.
    '-Wwrite-strings',
    # warn whenever a pointer is cast to remove a type qualifier from the target type*.
    '-Wcast-qual',
    # warn whenever a switch statement has an index of enumerated type
    # and lacks a case for one or more of the named codes of that enumeration*.
    '-Wswitch-enum',
    # warn if the compiler detects that code will never be executed*.
    '-Wunreachable-code',
    # warn if anything is declared more than once in the same scope, even in cases where multiple declaration is
    # valid and changes nothing
    '-Wredundant-decls',
    # warn if an undefined identifier is evaluated in an #if directive. Such identifiers are replaced with zero
    '-Wundef',
    '-Wendif-labels',
    # warn if a user-supplied include directory does not exist
    '-Wmissing-include-dirs',
    # also warn about uses of format functions that represent possible security problems
    '-Wformat-security',
    # also warn about strftime formats that may yield only a two-digit year
    '-Wformat-y2k',
    # warn for obsolescent usages, according to the C Standard, in a declaration
    '-Wold-style-declaration',
    # Warn if an old-style function definition is used
    '-Wold-style-definition',
    # Warn if a function is declared or defined without specifying the argument types
    '-Wstrict-prototypes',
    # Warn if a global function is defined without a previous prototype declaration
    '-Wmissing-prototypes',
]

target_gc = [
    # Target flags
    '-mabi=lp64d',
    '-march=rv64gc',  # opt out in future
    '-mcmodel=medany',
]

target_imac = [
    # Target flags
    '-mabi=lp64',
    '-march=rv64imac_zicsr_zifencei',  # opt out in future
    '-mcmodel=medany',
]


@conf
def add_gcc_flags(conf):
    conf.env.append_unique('CFLAGS', common_flags)
    # Select the target ARCH and put flags accordingly. If nothing is supplied
    # by default we build for E51
    if conf.env.arch == 'rv64imac':
        conf.env.append_unique('CFLAGS', target_imac)
    elif conf.env.arch == 'rv64gc_zicsr_zifencei':
        conf.env.append_unique('CFLAGS', target_gc)
    else:
        Logs.warn('WARNING: gcc_flags tool: ctx.env.ARCH not set, defaulting to rv64imac')
        conf.env.append_unique('CFLAGS', target_imac)

    # This is global as we are using GNU C extensions
    conf.env.append_unique('CFLAGS', ['-std=gnu17'])

@conf
def add_wall_gcc_flags(conf):
    conf.env.append_unique('CFLAGS', wall_flags)

@conf
def add_wextra_gcc_flags(conf):
    conf.env.append_unique('CFLAGS', wextra_flags)

@conf
def add_pedantinc_gcc_flags(conf):
    conf.env.append_unique('CFLAGS', pedantic_flags)


def configure(conf):
    conf.add_gcc_flags()
    #conf.add_wall_gcc_flags()
    #conf.add_wextra_gcc_flags()
    #conf.add_pedantinc_gcc_flags()
