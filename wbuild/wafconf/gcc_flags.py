# !/usr/bin/python
#
# Author: Francescodario Cuzzocrea <bosconovic@gmail.com>
# Date: 10/05/2024

from waflib.Configure import conf

common_compiler_flags = [
    # Generate proper debug symbols for GDB and TRACE32
    '-ggdb3',
    '-gdwarf-2',
    # Place each function or data in a separate section, so the linker can discard unused ones
    '-fdata-sections',
    '-ffunction-sections',
    # Always run GCC static analyzer
    '-fanalyzer',
    # Put global and static data smaller than 8 bytes into a special section
    '-msmall-data-limit=8',
    # Do not assume that unaligned memory references are handled by the system
    '-mstrict-align',
    # GCC fancy output
    '-fmessage-length=0',
    '-fdiagnostics-color=always',
]

wall_flags = [
    # This section contains the warnings usually coming from  '-Wall',
    '-Waddress',
    '-Wbool-compare',
    '-Wbool-operation',
    '-Wchar-subscripts',
    '-Wcomment',
    '-Wenum-compare',
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
    '-Wswitch',
    '-Wtautological-compare',
    '-Wtrigraphs',
    '-Wuninitialized',
    '-Wunused-label',
    '-Wunused-value',
    '-Wunused-variable',
    '-Wunused-function',
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
    # warn whenever a switch statement has an index of enumerated type
    # and lacks a case for one or more of the named codes of that enumeration*.
    '-Wswitch-enum',
    # Warn whenever a switch statement does not have a default case
    '-Wswitch-default',
    # warn if the compiler detects that code will never be executed*.
    '-Wunreachable-code',
    # warn if anything is declared more than once in the same scope,
    # even in cases where multiple declaration is valid and changes nothing
    '-Wredundant-decls',
    # warn if an undefined identifier is evaluated in an #if directive.
    # Such identifiers are replaced with zero
    '-Wundef',
    '-Wendif-labels',
    # warn if a user-supplied include directory does not exist
    '-Wmissing-include-dirs',
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
    # Warn when a declaration does not specify a type
    '-Wimplicit-int',
    # Warn whenever a function is used before being declared
    '-Wimplicit-function-declaration',
    # Warn if an extern declaration is encountered within a function
    '-Wnested-externs',
    # Warn if padding is included in a structure, either to align an element
    # of the structure or to align the whole structure.
    # Sometimes when this happens it is possible to rearrange the fields of the
    # structure to reduce the padding and so make the structure smaller
    '-Wpadded',
    # Warn if a structure is given the packed attribute, but the packed attribute
    # has no effect on the layout or size of the structure
    '-Wpacked',
    # Warn about functions which might be candidates for format attributes
    '-Wmissing-format-attribute',
    # Warn about functions which might be candidates for attribute noreturn
    '-Wmissing-noreturn',
    # Warn if a global function is defined without a previous declaration
    '-Wmissing-declarations',
    # Warn if any functions that return structures or unions are defined or called
    '-Waggregate-return',
    # Warn when a comparison between signed and unsigned values could produce an
    # incorrect result when the signed value is converted to unsigned
    '-Wsign-compare',
    # Warn whenever a pointer is cast such that the required alignment of the target is increased
    '-Wcast-align=strict',
    # Warn whenever a function call is cast to a non-matching type
    '-Wbad-function-cast',
    # Warn when a #pragma directive is encountered which is not understood by GCC
    '-Wunknown-pragmas',
    # Warn if the type of main is suspicious
    '-Wmain',
]

security_flags = [
    # check for format string problems
    '-Wformat=2',
    # check for *printf overflow
    '-Wformat-overflow=2',
    # check for *nprintf potential truncation
    '-Wformat-truncation=2',
    # If -Wformat is specified, also warn if the format string is not a string
    # literal and so cannot be checked, unless the format function takes its format
    # arguments as a va_list
    '-Wformat-nonliteral',
    # also warn about uses of format functions that represent possible security problems
    '-Wformat-security',
    # Warn (in format functions) about sign mismatches between the format specifiers
    # and actual parameters
    '-Wformat-signedness',
    # Warn if dereferencing a NULL pointer may lead to erroneous or undefined behavior
    '-Wnull-dereference',
    # Warn when not issuing stack smashing protection for some reason
    '-Wstack-protector',
    # Warn when the compiler optimizes based on the assumption that signed overflow does not occur
    '-Wstrict-overflow=3',
    # Warn whenever a trampoline is generated (will probably create an executable stack)
    '-Wtrampolines',
    # don't use alloca(), or limit it to "small" sizes
    '-Walloca',
    # don't use variable length arrays, or limit them to "small" sizes
    '-Wvla',
    # Warn if an array is accessed out of bounds. Note that it is very limited
    # and will not catch some cases which may seem obvious
    '-Warray-bounds=2',
    # Warn of prototypes causing type conversions different from what
    # would happen in the absence of prototype
    '-Wtraditional-conversion',
    # Warn if left shift of a signed value overflows
    #'-Wshift-overflow=2'
    # warn whenever a pointer is cast to remove a type qualifier from the target type*.
    '-Wcast-qual',
    # Under the control of Object Size type, warn about buffer overflow
    # in string manipulation functions like memcpy and strcpy
    '-Wstringop-overflow=4',
    # Warn if a prototype causes a type conversion that is different from what would
    # happen to the same argument in the absence of a prototype
    '-Wconversion',
    # Warn if conversion of the result of arithmetic might change the value even
    # though converting the operands cannot. Note: will probably introduce lots of warnings
    '-Warith-conversion',
    # checks if pointers still refer to "dead" variables
    '-Wdangling-pointer=2',
    # Obvious
    '-Wuse-after-free=3',
]

bad_logic_flags = [
    '-Wlogical-op',
    '-Wduplicated-cond',
    '-Wduplicated-branches',
]

@conf
def add_gcc_flags(conf):
    conf.env.append_unique('CFLAGS', common_compiler_flags)
    conf.env.append_unique('CFLAGS', '-mcmodel=medany')
    # Select the target ARCH and put flags accordingly.
    if conf.env.ARCH == 'rv64imac':
        conf.env.append_unique('CFLAGS', '-march=rv64imac_zicsr_zifencei')
        conf.env.append_unique('CFLAGS', '-mabi=lp64')
    elif conf.env.ARCH == 'rv64imafdc':
        conf.env.append_unique('CFLAGS', '-march=rv64imafdc_zicsr_zifencei')
        conf.env.append_unique('CFLAGS', '-mabi=lp64d')

    # Same set of flags are also applied to GAS (GNU ASsembler)
    conf.env.append_unique('ASFLAGS', conf.env.CFLAGS)

    # This is global as we are using GNU C extensions
    conf.env.append_unique('CFLAGS', ['-std=gnu11'])

@conf
def add_wall_gcc_flags(conf):
    conf.env.append_unique('CFLAGS', wall_flags)

@conf
def add_wextra_gcc_flags(conf):
    conf.env.append_unique('CFLAGS', wextra_flags)

@conf
def add_pedantinc_gcc_flags(conf):
    conf.env.append_unique('CFLAGS', pedantic_flags)

@conf
def add_bad_logic_flags(conf):
    conf.env.append_unique('CFLAGS', bad_logic_flags)

@conf
def add_security_flags(conf):
    conf.env.append_unique('CFLAGS', security_flags)

def configure(conf):
    conf.add_gcc_flags()
    #conf.add_wall_gcc_flags()
    #conf.add_wextra_gcc_flags()
    #conf.add_pedantinc_gcc_flags()
    #conf.add_security_flags()
