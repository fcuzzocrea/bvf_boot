# !/usr/bin/env python

# pylint: disable=too-many-statements, unused-argument, invalid-name, missing-class-docstring, too-few-public-methods
# -*- coding: utf-8 -*-
# Author: Francescodario Cuzzocrea <bosconovic@gmail.com>

import git
import os
import yaml
from waflib import Errors, Logs

from wbuild.support import error_support


def init_app_configure_stage(ctx, project, project_keys):
    """
    The init_app_configure_stage function checks if the core context variables which are needed by the build system
    are correctly set by the application, then appends to version number the current git revision, to maintain
    traceability of the code which is being built. The init_app_configure_stage function MUST be the first function
    which is called by the app at the configure stage. The core context variable which are needed by the build system
    are:

       * ctx.env.name: name of the application which is calling this function.
       * ctx.env.codename: codename of the application. Must be a girl name. Please exercise your fantasy.
       * ctx.env.version: version of the application
       * ctx.env.arch: architecture for which we are building

    Example usage:

        # Save into WAF context the variable which are needed by the common build system
        ctx.env.name = APPNAME
        ctx.env.codename = CODENAME
        ctx.env.version = VERSION
        ctx.env.arch = ctx.options.arch

        # Initialize the build system
        init_app_configure_stage(ctx)

    Args:
        :param ctx: The WAF context
        :param project: handle to project.yml
        :param project_keys: list of the project keys
    """
    if not ctx.env.name:
        raise Errors.ConfigurationError(error_support.CONFIGURATION_ERROR + 'Please set an the ctx.env.name environment variable.')

    if not ctx.env.codename:
        raise Errors.ConfigurationError(error_support.CONFIGURATION_ERROR +
                                        'Please set the ctx.env.codename environment variable. Only girl names are '
                                        'allowed as codenames.')

    if not ctx.env.version:
        raise Errors.ConfigurationError(error_support.CONFIGURATION_ERROR + 'Please consider adding the semantic versioning tool and set the '
                                                                            'ctx.env.version environment variable for this application.')

    # Initialize git repo object in the current dir.
    git_repo = git.Repo(ctx.path.get_bld().relpath(), search_parent_directories=False)
    git_revision = git_repo.git.describe('--always', '--dirty')
    ctx.env.revision = ctx.env.version + '~' + git_revision


def parse_project_keys(ctx):
    """
    The parse_project_keys function open the project.yml which is present in the project root directory and returns as
    an output the handler to the file and the list of the keys found inside the yml, for later usage.
    The project.yml file MUST be placed into the project root directory. This function MUST be executed after the
    init_app_configure_stage but before any other function which takes as an input the project.yml and/or its keys.

    Example usage in wscript:

        # Setup environment variables needed by the build system
        ctx.env.name = APPNAME
        ctx.env.codename = CODENAME
        ctx.env.version = VERSION

        # Iniit the build system
        init_app_configure_stage(ctx)

        # Parse project.yml
        [project, project_keys] = parse_project_keys(ctx)

    Args:
        :param ctx: The WAF context

    Rets:
        :return project: handle to project.yml
        :return project_keys: list of the project keys
    """
    if os.path.exists(os.path.join(ctx.path.get_bld().relpath(), 'project.yml')):
        project = yaml.safe_load(open(os.path.join(ctx.path.get_bld().relpath(), 'project.yml')))
        try:
            project_keys = list(project.keys())
        except AttributeError as exc:
            project_keys = []
        return project, project_keys
    else:
        raise Errors.ConfigurationError(error_support.CONFIGURATION_ERROR +
                                        'Invalid path of project.yml. Please put it into the project root folder.')


def setup_common_app_headers(ctx):
    """
    The setup_common_app_headers writes config header for this project - at this stage we have already parsed the
    options, so we have everything that is needed to write common defines.
    If user want to add more, can always do that in project wscript.
    This function can only be called after loading the C WAF tool, otherwise WAF is not aware of the fact that he has to
    write a header file for a C program.
    It is strongly advised to call this function AFTER defining any custom define needed by the particular application,
    as we are doing the call to write_config_header into this function.

    The setup_common_app_headers function is private and it is not meant to be called outside this module.

    Args:
        :param ctx: The WAF context
    """

    ctx.define('APP_GIT_REV', ctx.env.revision)
    ctx.define('APP_CODENAME', ctx.env.codename)
    ctx.define('APP_NAME', ctx.env.name)
    ctx.write_config_header('generated_headers/' + ctx.env.name + '_config.h', top=True, remove=True)


def load_tools(ctx):
    """
    The load_tools function is responsible for loading the right tool (compiler, flags, etc) according to the given
    architecture

    Example usage:
        # Save into WAF context the variable which are needed by the common build system
        ctx.env.arch = ctx.options.arch

        # Load appropriate tools for the arch (compiler, etc)
        load_tools(ctx)

    Args:
        :param ctx: The WAF context
    """
    if ctx.env.arch == 'rv64imac' or ctx.env.arch == 'rv64gc':
        # Load common stuffs
        ctx.load('gcc_flags c', tooldir="wbuild/wafconf")

        if ctx.options.programmer == 'openocd':
            # Load openocd
            ctx.load('openocd', tooldir='wbuild/wafconf')

        if ctx.options.programmer == 'fpgenprog':
            # Load fpgenprog
            ctx.load('fpgenprog', tooldir='wbuild/wafconf')

        if ctx.env.platform == 'baremetal' or ctx.env.platform == 'freertos':
            # Load bare-metal toolchain
            ctx.load('riscv64gcc', tooldir="wbuild/wafconf")
        elif ctx.env.platform == 'rtems':
            # Load rtems
            ctx.load('riscv64rtems', tooldir="wbuild/wafconf")
        else:
            raise Errors.ConfigurationError(
                error_support.CONFIGURATION_ERROR + ctx.env.platform + ' is not supported, supported platforms are bare-metal and rtems')
    else:
        raise Errors.ConfigurationError(
            error_support.CONFIGURATION_ERROR + ctx.env.arch + ' is not supported, supported arch is rv64 only')


def configure_release(ctx):
    """
    The configure_release function is responsible for configuring the release environment.

    configure_release is not meant to be called directly, but it is meant to be passed to the setenv_from_base function.

    Args:
        :param ctx: The WAF context
    """
    ctx.env.append_unique('CFLAGS', '-DRELEASE')


def configure_debug(ctx):
    """
    The configure_debug function is responsible for configuring the debug environment.

    configure_debug is not meant to be called directly, but it is meant to be passed to the setenv_from_base function.

    Args:
        :param ctx: The WAF context
    """
    ctx.env.append_unique('CFLAGS', '-DDEBUG')



def setenv_from_base(ctx, env_name, env_config, project, project_keys, appname):
    """
    The configure_release function is responsible for configuring the release environment.

    This function is meant to be called ONLY from an application build, not from a library build.
    Library handling will be added in the future.

    Example usage:

        # Setup additional environments
        setenv_from_base(ctx, 'release', configure_release, project, project_keys)
        setenv_from_base(ctx, 'debug', configure_debug, project, project_keys)
        setenv_from_base(ctx, 'unittest', configure_ut, project, project_keys)

    Args:
        :param ctx: The WAF context
        :param env_name: Name of the environment we want to configure
        :param env_config: Pointer to the function which is called during environment configuration
        :param project: Handle to project.yml
        :param project_keys: List of keys present in project.yml
        :param appname: Name of the application

    """
    # Parse CFLAGS
    parse_common_flags(ctx, project, project_keys, appname)

    # We now write common application defines in the sysctrlapp_config.h header. Do note that this must be called after
    # loading c and toolchain tools, otherwise WAF is not aware we are using C
    setup_common_app_headers(ctx)

    # Keep track of our original environment
    base_env = ctx.env
    base_variant = ctx.variant

    # Setup new environment
    ctx.setenv(env_name, env=base_env)
    env_config(ctx)

    # Restore original
    ctx.setenv(base_variant, base_env)


def append_platform_flags(ctx, flags_variable):
    """
    The append_platform_flags is responsible for adding platform (OS) dependent flags.
    Currently supported platforms are:

        - baremetal
        - rtems

    parse_common_flags is private, and it is not meant to be called outside this module.

    Args:
        :param ctx: The WAF context
        :param flags_variable: Context variable in which the flags will be appended
    """
    # Globally define platform dependent flags
    if ctx.env.platform == 'baremetal':
        ctx.env.append_unique(flags_variable, '-DBAREMETAL')
    if ctx.env.platform == 'rtems':
        ctx.env.append_unique(flags_variable, '-DRTEMS')


def parse_library_flags(ctx, project, project_keys, libname):
    """
    The parse_library_flags is responsible for parsing cflags for a given library.
    cflags are added to the variable ctx.env.CFLAGS_${LIBNAME}.

    parse_library_flags is meant to be used only by libraries.

    Example usage:

        # Parse yml file for the inline library build
        [project, project_keys] = parse_project_keys(ctx)

        # Parse library cflags
        parse_library_flags(ctx, project, project_keys, LIBNAME)

    Args:
        :param ctx: The WAF context
        :param project: Handle to project.yml
        :param project_keys: List of keys present in project.yml
        :param libname: Name of the library
    """
    if ctx.options.standalone:
        # Define here platform dependent flags for the library when it is compiled
        # in standalone
        append_platform_flags(ctx, 'CFLAGS_' + libname.upper())

    if project_keys:
        if 'cflags' in project_keys:
            cflags_keys = (list(project['cflags']))
            if 'local' in cflags_keys:
                ctx.env.append_unique('CFLAGS_' + libname.upper(), list(project['cflags']['local']))


def parse_common_flags(ctx, project, project_keys, appname):
    """
    The parse_common_flags is responsible for parsing asflags and cflags.
    asflags are added to the assembler preprocessor, while cflags are added to the C preprocessor.
    Four different types of cflags can be appended to the build:

      - cflags_global: global cflags needed by library or application
      - cflags_local: local cflags needed by library or application
      - cflags_debug: cflags appended for debug builds
      - cflags_release: cflags appended for release build
      - cflags_release_optional: optional cflags appended for release build

    parse_common_flags is private, and it is not meant to be called outside this module.

    Args:
        :param ctx: The WAF context
        :param project: Handle to project.yml
        :param project_keys: List of keys present in project.yml
        :param appname: Name of the application
    """
    # HACK - I am abusing ctx variables to avoid using global variables.
    if project_keys:
        if 'cflags' in project_keys:
            cflags_keys = (list(project['cflags']))
            if 'global' in cflags_keys:
                ctx.env.cflags_global = (list(project['cflags']['global']))
            if 'local' in cflags_keys:
                ctx.env.cflags_local = (list(project['cflags']['local']))

    if ctx.env.cflags_global:
        ctx.env.append_unique('CFLAGS', ctx.env.cflags_global)

    if ctx.env.cflags_local:
        ctx.env.append_unique('CFLAGS_' + appname.upper(), ctx.env.cflags_local)

    # Globally define platform dependent flags
    append_platform_flags(ctx, 'CFLAGS')


def write_common_library_defines(ctx, libname):
    """
    The write_common_library_defines is responsible for appending the USES_LIBNAME define and the library version in
    the libname_autoconfig.h header.

    Example usage:

        write_common_library_defines(ctx, LIBNAME)

    where LIBINAME = libpippo

    Args:
        :param ctx: The WAF context
        :param libname: name of the library
    """
    ctx.define('USES_' + libname.upper(), 1)
    ctx.define(libname.upper() + '_VERSION', ctx.env.version)
    ctx.write_config_header('generated_headers/' + libname + '_autoconfig.h', top=True, remove=True)
