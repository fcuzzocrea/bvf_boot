# !/usr/bin/env python

# pylint: disable=too-many-statements, unused-argument, invalid-name, missing-class-docstring, too-few-public-methods
# -*- coding: utf-8 -*-
# Author: Francescodario Cuzzocrea <bosconovic@gmail.com>

#import git
import os
import yaml
from waflib import Errors, Logs

wafbuild_home = os.environ.get('BUILD_SYSTEM_PATH')


def init_app_configure_stage(ctx, project, project_keys) -> None:
    # The init_app_configure_stage function checks if the core context variables
    # which are needed by the build system are correctly set by the application, then appends
    # to version number the current git revision, to maintain traceability of the code which is
    # being built. The init_app_configure_stage function MUST be the first function
    # which is called by the app at the configure stage.
    # The core context variable which are needed by the build system are:
    #
    #    * ctx.env.name: name of the application which is calling this function.
    #    * ctx.env.codename: codename of the application. Must be a girl name.
    #                        Exercise your fantasy.
    #    * ctx.env.version: version of the application
    #    * ctx.env.ARCH: architecture for which we are building
    #
    # Example usage:
    #
    #     # Save into WAF context the variable which are needed by the common build system
    #     ctx.env.name = APPNAME
    #     ctx.env.codename = CODENAME
    #     ctx.env.version = VERSION
    #     ctx.env.ARCH = ctx.options.arch
    #
    #     # Initialize the build system
    #     init_app_configure_stage(ctx)
    #
    # Args:
    #     :param ctx: The WAF context
    #     :param project: handle to project.yml
    #     :param project_keys: list of the project keys

    required_env_vars = {
        'name': 'Please set the ctx.env.name environment variable.',
        'codename': 'Please set the ctx.env.codename environment variable.' +
                    ' Only girl names are allowed as codenames.',
        'version': 'Please consider adding the semantic versioning tool and set ' +
                   'the ctx.env.version environment variable for this application.',
        'ARCH': 'Please set the ctx.env.ARCH environment variable for this project.',
    }

    for var, error_message in required_env_vars.items():
        if not getattr(ctx.env, var):
            ctx.fatal(error_message)

    ctx.env.platform = ''.join(project.get('platform', ''))
    if not ctx.env.platform:
        ctx.fatal('Please set the platform variable in the project configuration.')

    ctx.env.is_bootloader = ''.join(project.get('is_bootloader', ''))
    if not ctx.env.is_bootloader:
        ctx.fatal('Please set the is_bootloader variable in the project.yml.')

    # If we detect the user put the source code under version control, append the
    # sha to the revision
    #try:
    #    git_repo = git.Repo(ctx.path.get_bld().relpath(), search_parent_directories=False)
    #    git_revision = git_repo.git.describe('--always', '--dirty')
    #except git.exc.InvalidGitRepositoryError:
    #    git_revision = 'nosrcrev'
    git_revision = 'nosrcrev'
    ctx.env.git_rev = f'{ctx.env.version}~{git_revision}'


def parse_project_keys(ctx) -> list:
    # The parse_project_keys function open the project.yml which is present in the project
    # root directory and returns as an output the handler to the file and the list of the keys
    # found inside the yml, for later usage.
    # The project.yml file MUST be placed into the project root directory.
    # This function MUST be executed after the init_app_configure_stage but before any other
    # function which takes as an input the project.yml and/or its keys.
    #
    # Example usage in wscript:
    #
    #     # Setup environment variables needed by the build system
    #     ctx.env.name = APPNAME
    #     ctx.env.codename = CODENAME
    #     ctx.env.version = VERSION
    #
    #     # Iniit the build system
    #     init_app_configure_stage(ctx)
    #
    #     # Parse project.yml
    #     [project, project_keys] = parse_project_keys(ctx)
    #
    # Args:
    #     :param ctx: The WAF context
    #
    # Rets:
    #     :return project: handle to project.yml
    #     :return project_keys: list of the project keys

    project_path = os.path.join(ctx.path.get_bld().relpath(), 'project.yml')

    if os.path.exists(project_path):
        with open(project_path, encoding='utf-8') as f:
            project = yaml.safe_load(f) or {}

        project_keys = list(project.keys())
        return project, project_keys

    return None, []


def setup_common_app_headers(ctx)-> None:
    # The setup_common_app_headers writes config header for this project - at this stage
    # we have already parsed the options, so we have everything that is needed to write
    # common defines.
    # If user want to add more, can always do that in project wscript.
    # This function can only be called after loading the C WAF tool, otherwise WAF is not
    # aware of the fact that he has to write a header file for a C program.
    # It is strongly advised to call this function AFTER defining any custom define needed
    # by the particular application, as we are doing the call to write_config_header into
    # this function.
    #
    # The setup_common_app_headers function is private and it is not meant to be called outside
    # this module.
    #
    # Args:
    #     :param ctx: The WAF context


    # Define common application constants
    for var in ['git_rev', 'codename', 'name']:
        ctx.define(f'APP_{var.upper()}', getattr(ctx.env, var))

    # Define HW_VERSION based on the hw_version option
    hw_version_mapping = {
        'ICICLE': 0,
        'CORE3': 1
    }

    hw_version = hw_version_mapping.get(ctx.options.hw_version)
    if hw_version is not None:
        ctx.define('HW_VERSION', hw_version)
    else:
        ctx.fatal('No hardware revision defined.')

    # Write the configuration header
    config_header_path = os.path.join('generated_headers', f'{ctx.env.name}_config.h')
    ctx.write_config_header(config_header_path, top=True, remove=True)


def parse_libraries_options(ctx, project, project_keys) -> None:
    # The parse_libraries_options is responsible for configuring the (optional) additional
    # library used by an app.
    # parse_libraries_options supports inlining either WAF based libraries or Makefile based
    # libraries.
    # It also support adding prebuilt static library to the build.
    # To add a WAF based library to the build, add this snippet of code to your project.yml:
    #
    #   libraries:
    #     libpluto:
    #       build_system: waf
    #       path: lib
    #       options:
    #         my_option_1:
    #         my_option_2:
    #       uses:
    #       - my_deps_1
    #       - my_deps_2
    #
    # To add a Makefile based library to the build, add this snippet of code to your project.yml:
    #
    #   libraries:
    #     libgoofy:
    #       build_system: make
    #       path: ext
    #       options:
    #         env_vars: CROSS_COMPILE=riscv64-unknown-elf-
    #         make_target: PLATFORM=core3
    #         install_path: ../../ext/libgoofy/build/platform/core3/lib
    #
    # The make command will be invoked at the prebuild stage, in the following fashion:
    #
    #     $env_vars make $make_target install $install_path
    #
    # The install_path arguments is the path in which the libray is installed, and it is
    # the path which will be passed to the -L command of the linker, at application
    # linking stage.
    #
    # Allowed entries for path are either 'lib' for internal dependencies or 'ext' for
    # 3rd party dependencies.
    # The library folder MUST begin with the 'lib' folder, so ext/libpluto, ext/libpippo,
    # lib/libdonald are legal paths, while ext/minnie it is not legal.
    #
    # The function parses also the list of prebuilt libraries which are (optionally) added to
    # the build.
    # To add a prebuilt library add this snippet to your project.yml:
    #
    #   libraries:
    #     prebuilt:
    #      - libdaisy
    #
    # Args:
    #     :param ctx: The WAF context
    #     :param project: Handle to project.yml
    #     :param project_keys: List of keys present in project.yml

    if 'libraries' not in project_keys:
        return

    libraries = project['libraries']
    if 'inline' in libraries:
        for library, library_keys in libraries['inline'].items():
            build_system = library_keys.get('build_system')
            if not build_system:
                ctx.fatal(f'Please specify the build system for {library}')
            _configure_library(ctx, project, library, library_keys, build_system)

    if 'prebuilt' in libraries:
        _configure_prebuilt_libraries(ctx, project)

    _library_configure_post_checks(ctx)


def _configure_library(ctx, project, library, library_keys, build_system):
    if build_system == 'waf':
        _configure_waf_library(ctx, project, library, library_keys)
    else:
        ctx.fatal(f'{library} build system not supported')


def _get_library_path(project, library, library_keys):
    return os.path.join(library_keys.get('path', ''), library)


def _configure_waf_library(ctx, project, library, library_keys) -> None:
    # The configure_waf_library functions parses external WAF library options from the project.yml.
    # It also appends the library to the global USES context variable.
    # It then adds a USES_LIBINAME #define entry into the self generated app config header file.
    #
    # configure_waf_library it is a private function and it is not meant to be called outside
    # this module.
    #
    # Args:
    #     :param ctx: The WAF context
    #     :param project: Handle to project.yml
    #     :param library: current library which is being configured
    #     :param library_keys: List of keys present in project.yml for the library which is
    #                          currently being configured

    library_path = _get_library_path(project, library, library_keys)
    if not library_path:
        ctx.fatal(f'Please set the {library} library path')

    options = library_keys.get('options', {})
    for key, val in options.items():
        setattr(ctx.options, key, val)
        if key == 'uses':
            ctx.env.append_unique(f'USES_{library.upper()}', val)

    wscript_path = os.path.join(library_path, 'wscript')
    if os.path.exists(wscript_path):
        Logs.pprint('CYAN', f'Configuring {library}...')
        ctx.env.append_unique('USES', [library])
        ctx.recurse(library_path, mandatory=True, once=True)
    else:
        ctx.fatal(f'Cant read {library} wscript')


def _configure_prebuilt_libraries(ctx, project) -> None:
    # The configure_prebuilt_libraries function appends the static lib paths to the
    # LIB_PATHS context variable which is then passed to the linker command line.
    # Since we are using the resolve WAF module, we know that libraries are always
    # resolved in a precise location, so the implementation is quite easy.
    #
    # configure_prebuilt_libraries it is a private function and it is not meant to be
    # called outside this module.
    #
    # Args:
    #     :param ctx: The WAF context
    #     :param project: Handle to project.yml
    #
    # For the prebuilt libs, waf does not know the path, but we know that
    # they are resolved always in the same location... So we just read the
    # list and append the location

    prebuilt_libs = project['libraries'].get('prebuilt', [])
    for library in prebuilt_libs:
        ctx.env.append_unique('LIB_PATHS', os.path.join(ctx.path.bld_dir(),
                                                        'resolve_symlinks', library))


def _library_configure_post_checks(ctx) -> None:
    # The library_configure_post_checks function makes sure that if a library
    # is added to the list of the libraries to be used, it is also added to the
    # link order project.yml entry.
    # Linking order is enforced in the build system for simplicity of design and
    # also because linking order is frequently cause of issues embedded projects.
    # So we have decided to enforce link order whenever linking an external library
    # is required.
    #
    # @TODO: this function for now is very basic and it is not taking into account prebuilt
    #        libraries which needs to be added to the link order entry too
    #
    # library_configure_post_checks it is a private function and it is not meant to be called
    # outside this module.
    #
    # Args:
    #     :param ctx: The WAF context

    if ctx.env.LIBS is None and ctx.env.LIB_PATHS:
        ctx.fatal('You are setting link order but you are not declaring libraries')
    if ctx.env.LIB_PATHS is None and ctx.env.LIBS:
        ctx.fatal('You want to link to some libraries but you are not specifying link order')


def load_tools(ctx) -> None:
    # The load_tools function is responsible for loading the right tool (compiler, flags, etc)
    # according to the given architecture.
    #
    # Example usage:
    #     # Save into WAF context the variable which are needed by the common build system
    #     ctx.env.ARCH = ctx.options.arch
    #
    #     # Load appropriate tools for the arch (compiler, etc)
    #     load_tools(ctx)
    #
    # Args:
    #     :param ctx: The WAF context

    # Define the base tool directory
    tool_dir = os.path.join(wafbuild_home, 'wafconf')

    ctx.load('clang_compilation_database')
    ctx.load('clang_format', tooldir=tool_dir)

    def _load_common_embedded_tools():
        ctx.load('gcc_flags c', tooldir=tool_dir)
        ctx.load('fpgenprog', tooldir=tool_dir)
        ctx.load('openocd', tooldir=tool_dir)

    if ctx.env.ARCH in ('rv64imac', 'rv64imafdc'):
        _load_common_embedded_tools()
        platform_tools = {
            'baremetal': 'riscv64gcc',
            'rtems': 'riscvrtems6',
        }
        platform_tool = platform_tools.get(ctx.env.platform)
        if platform_tool:
            ctx.load(platform_tool, tooldir=tool_dir)
        else:
            ctx.fatal(f'{ctx.env.platform} is not supported, supported platforms are bare-metal, RTEMS')
    elif ctx.env.ARCH == 'x86_64':
        ctx.load('gcc')
    else:
        ctx.fatal(f'{ctx.env.ARCH} is not supported, supported archs are rv64 and x86_64 only')


def configure_release(ctx) -> None:
    # The configure_release function is responsible for configuring the release environment.
    #
    # configure_release is not meant to be called directly, but it is meant to be passed to
    # the setenv_from_base function.
    #
    # Args:
    #     :param ctx: The WAF context

    if ctx.env.cflags_release:
        ctx.env.append_unique('CFLAGS', ctx.env.cflags_release)


def configure_debug(ctx) -> None:
    # The configure_debug function is responsible for configuring the debug environment.
    #
    # configure_debug is not meant to be called directly, but it is meant to be passed
    # to the setenv_from_base function.
    #
    # Args:
    #     :param ctx: The WAF context

    if ctx.env.cflags_debug:
        ctx.env.append_unique('CFLAGS', ctx.env.cflags_debug)


def setenv_from_base(ctx, env_name, env_config, project, project_keys, appname) -> None:
    # The setenv_from_base function is responsible for configuring the release environment.
    #
    # This function is meant to be called ONLY from an application build, not from a library build.
    # Library handling will be added in the future.
    #
    # Example usage:
    #
    #     # Setup additional environments
    #     setenv_from_base(ctx, 'release', configure_release, project, project_keys)
    #     setenv_from_base(ctx, 'debug', configure_debug, project, project_keys)
    #     setenv_from_base(ctx, 'unittest', configure_ut, project, project_keys)
    #
    # Args:
    #     :param ctx: The WAF context
    #     :param env_name: Name of the environment we want to configure
    #     :param env_config: Pointer to the function which is called during environment
    #                        configuration
    #     :param project: Handle to project.yml
    #     :param project_keys: List of keys present in project.yml
    #     :param appname: Name of the application

    _parse_common_flags(ctx, project, project_keys, appname)

    # Keep track of our original environment
    base_env = ctx.env
    base_variant = ctx.variant

    # Setup new environment
    ctx.setenv(env_name, env=base_env)
    env_config(ctx)

    # Restore original
    ctx.setenv(base_variant, base_env)


def _append_platform_flags(ctx, flags_variable) -> None:
    # The append_platform_flags is responsible for adding platform (OS) dependent flags.
    # Currently supported platforms are:
    #
    #     - baremetal
    #     - rtems
    #
    # parse_common_flags is private, and it is not meant to be called outside this module.
    #
    # Args:
    #     :param ctx: The WAF context
    #     :param flags_variable: Context variable in which the flags will be appended

    # Globally define platform dependent flags
    platform_flags = {
        'baremetal': '-D__BAREMETAL__',
        'rtems': '-D__OS_RTEMS__',
    }

    flag = platform_flags.get(ctx.env.platform)
    if flag:
        ctx.env.append_unique(flags_variable, flag)


def parse_library_flags(ctx, project, project_keys, libname) -> None:
    # The parse_library_flags is responsible for parsing cflags for a given library.
    # cflags are added to the variable ctx.env.CFLAGS_${LIBNAME}.
    #
    # parse_library_flags is meant to be used only by libraries.
    #
    # Example usage:
    #
    #     # Parse yml file for the inline library build
    #     [project, project_keys] = parse_project_keys(ctx)
    #
    #     # Parse library cflags
    #     parse_library_flags(ctx, project, project_keys, LIBNAME)
    #
    # Args:
    #     :param ctx: The WAF context
    #     :param project: Handle to project.yml
    #     :param project_keys: List of keys present in project.yml
    #     :param libname: Name of the library

    lib_cflags_var = f'CFLAGS_{libname.upper()}'

    if ctx.options.standalone:
        # Define here platform dependent flags for the library when it is compiled in standalone
        _append_platform_flags(ctx, lib_cflags_var)

    if 'cflags' in project_keys and 'local' in project['cflags']:
        ctx.env.append_unique(lib_cflags_var, project['cflags']['local'])


def _parse_common_flags(ctx, project, project_keys, appname) -> None:
    # The parse_common_flags is responsible for parsing asflags and cflags.
    # asflags are added to the assembler preprocessor, while cflags are added to
    # the C preprocessor.
    # Four different types of cflags can be appended to the build:
    #
    #   - cflags_global: global cflags needed by library or application
    #   - cflags_local: local cflags needed by library or application
    #   - cflags_debug: cflags appended for debug builds
    #   - cflags_release: cflags appended for release build
    #
    # parse_common_flags is private, and it is not meant to be called outside this module.
    #
    # @HACK - I am abusing ctx variables to avoid using global variables.
    #
    # Args:
    #     :param ctx: The WAF context
    #     :param project: Handle to project.yml
    #     :param project_keys: List of keys present in project.yml
    #     :param appname: Name of the application

    if not project_keys:
        return

    # Initialize flags
    flag_types = {
        'asflags': [],
        'cflags_global': [],
        'cflags_local': [],
        'cflags_debug': [],
        'cflags_release': [],
        'cflags_release_optional': []
    }

    # Parse assembler flags
    if 'asflags' in project_keys:
        flag_types['asflags'] = list(project.get('asflags', []))

    # Parse C compiler flags
    if 'cflags' in project_keys:
        cflags = project.get('cflags', {})
        flag_types['cflags_global'] = list(cflags.get('global', []))
        flag_types['cflags_local'] = list(cflags.get('local', []))
        flag_types['cflags_debug'] = list(cflags.get('debug', []))
        flag_types['cflags_release'] = list(cflags.get('release', []))
        flag_types['cflags_release_optional'] = list(cflags.get('release_optional', []))

    # Assign flags to ctx.env and append unique values
    for key, flags in flag_types.items():
        if flags:
            ctx.env[key] = flags
            if key == 'asflags':
                ctx.env.append_unique('ASFLAGS', flags)
            elif key.startswith('cflags'):
                ctx.env.append_unique('CFLAGS', flags)

    if flag_types['cflags_local']:
        ctx.env.append_unique(f'CFLAGS_{appname.upper()}', flag_types['cflags_local'])

    # Globally define platform dependent flags
    _append_platform_flags(ctx, 'CFLAGS')


def write_common_library_defines(ctx, libname) -> None:
    # The write_common_library_defines is responsible for appending the
    # USES_LIBNAME define and the library version in the libname_autoconfig.h header.
    #
    # Example usage:
    #
    #     write_common_library_defines(ctx, LIBNAME)
    #
    # where LIBINAME = libpippo
    #
    # Args:
    #     :param ctx: The WAF context
    #     :param libname: name of the library

    ctx.define(f'USES_{libname.upper()}', 1)
    ctx.define(f'{libname.upper()}_VERSION', ctx.env.version)

    # Write the configuration header
    ctx.write_config_header(
        os.path.join('generated_headers', f'{libname}_autoconfig.h'),
        top=True,
        remove=True
    )
