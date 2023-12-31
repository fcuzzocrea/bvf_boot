# !/usr/bin/env python

# pylint: disable=too-many-statements, unused-argument, invalid-name, missing-class-docstring, too-few-public-methods
# -*- coding: utf-8 -*-
# Author: Francescodario Cuzzocrea <bosconovic@gmail.com>

import yaml
import os
import subprocess

from waflib import Errors, Logs

from wbuild.support import error_support
from wbuild.support.common_support import post_build_stats, clangdb_ide_support, prepend_mss_header


def parse_linker_options(ctx, project, project_keys):
    """
    The parse_linker_options parses the board linker options from project.yml. It requires as an argument the handle
    to the project.yml and the list of keys extrapulated from project.yml.
    It sets up the linker script to be used by the application and sets the libraries linking order if requested.

    The parse_linker_options is a private function, and it is not meant to be called outside this module.

    Args:
        :param ctx: The WAF context
        :param project: Handle to project.yml
        :param project_keys: List of keys present in project.yml
    """
    if 'linker' in project_keys:
        linker_keys = project['linker']
        if 'script' in linker_keys:
            ctx.env.ld_script = project['linker']['script']
        else:
            raise Errors.ConfigurationError(error_support.CONFIGURATION_ERROR + 'Please declare at least the linker script in the linker field.')
        if 'order' in linker_keys:
            # Store the linking order in a tuple. This variable is then
            ctx.env.LIBS = tuple(project['linker']['order'])


def add_linker_options(ctx):
    """
    The add_linker_options add all the relevant linkflags to the ctx.env.LINKFLAGS global variable.
    In particular, it also let you select the desired linker script according to the ctx.env.ld_script global variable.

    The add_linker_options is a private function, and it is not meant to be called outside this module.

    Args:
        :param ctx: The WAF context
    """

    # Select the target ARCH and put flags accordingly. If nothing is supplied
    # by default we build for E51
    if ctx.env.arch == 'rv64imac':
        link_flags = ['-march=rv64imac', '-mabi=lp64']
    elif ctx.env.arch == 'rv64gc':
        link_flags = ['-march=rv64gc', '-mabi=lp64d']
    else:
        Logs.warn('WARNING: ctx.env.arch not set, defaulting to rv64imac')
        link_flags = ['-march=rv64imac', '-mabi=lp64']

    # To generate MAP file
    link_flags.extend(['-Wl,-Map=' + ctx.env.name + '.map'])

    # Sections garbage collection
    link_flags.extend(['-Wl,--gc-sections'])
                           
    if ctx.env.platform == 'baremetal':
        if not ctx.env.ld_script:
            ctx.fatal('Please provide the desired linker script in the ld_script env variable')

        # Do not use default CRT and use newlib nano
        link_flags.extend(['-nostartfiles', '--specs=nano.specs'])

        # Append linker script path to LDFLAGS
        link_flags.extend(['-L../../confs/linker/'])
        link_flags.extend(['-T' + ctx.env.ld_script + '.ld'])

    ctx.env.append_unique('EXTRA_LDFLAGS', link_flags)


def parse_and_add_linker_options(ctx, project, project_keys):
    """
    The parse_and_add_linker_options parses the board linker options from project.yml. It requires as an argument the handle
    to the project.yml and the list of keys extrapulated from project.yml. In particular, it sets up the linker script
    to be used by the application and sets the libraries linking order if requested.
    If you are enforcing linking order, remember to add the lib=ctx.env.LIBS variable to your application ctx.program.
    The function then configures the linker script to be used.

    Example snippet of project.yml:

        linker:
          script: lim
          order:
            - goofy
            - daisy
            - donald

    Args:
        :param ctx: The WAF context
        :param project: Handle to project.yml
        :param project_keys: List of keys present in project.yml
    """
    parse_linker_options(ctx, project, project_keys)
    add_linker_options(ctx)


def file_existance_check(ctx, list):
    """
    This function is used to check if the source files declared in project.yml exist in the current path. If not, it
    raises a fatal error.

    :param ctx: The WAF context
    :param list: The list of source files to check
    """
    for file in list:
        if not os.path.isfile(ctx.path.relpath() + '/' + file):
            ctx.fatal('Source file ' + ctx.path.abspath() + '/' + file + ' does not exist')


def parse_project_sources(ctx, path, name):
    """
    The parse_project_sources function appends the list of source files and the include paths found in the provided
    sources.yml.
    The function is also recursive, this means that if your provide a module entry in project.yml, it will enter into
    the supplied module folder, parse the sources.yml and append it to the list of includes and sources of the parent.

    In the case the function is called by an application, the name argument must be set to None, while in the case the
    function is called by a library, the name argument must be set to libname.

    For example:

      - app:
          parse_project_sources(ctx, os.path.join(ctx.path.get_bld().relpath(), 'src'), None)

      - library:
          parse_project_sources(ctx, ctx.path.get_bld().relpath(), LIBNAME.upper())

    where LIBNAME = libpippo

    Args:
        :param ctx: The WAF context
        :param path: Path to sources.yml
        :param name: Optional argument, name. To be set to None in case of the caller is an app, otherwise to libname
                     in case the caller is a library.
    """
    if os.path.exists(os.path.join(path, 'sources.yml')):
        srcs = yaml.safe_load(open(os.path.join(path, 'sources.yml')))
        for value in srcs:
            if value == 'includes':
                if name:
                    ctx.env.append_unique('INCLUDES' + '_' + name, srcs['includes'])
                else:
                    ctx.env.append_unique('INCLUDES', srcs['includes'])
            elif value == 'files':
                file_existance_check(ctx, srcs['files'])
                if name:
                    ctx.env.append_unique('SOURCES' + '_' + name, srcs['files'])
                else:
                    ctx.env.append_unique('SOURCES', srcs['files'])
            elif value == 'modules':
                app_modules = srcs['modules']
                for module in app_modules:
                    if os.path.exists(os.path.join(path, module)):
                        parse_project_sources(ctx, os.path.join(path, module), name)
                    else:
                        Errors.ConfigurationError(error_support.CONFIGURATION_ERROR + os.path.join(path, module) + ' does not contain any sources.yml')
            else:
                pass
    else:
        raise Errors.ConfigurationError(
            error_support.CONFIGURATION_ERROR + os.path.join(path) + ' does not contain any sources.yml')


def add_inline_libs_to_build(ctx, project, project_keys):
    """
    The add_inline_libs_to_build recurse trough each WAF inline library added to the project and recursively calls the
    build functions present in the respective wscripts, building the target libraries.

    Example usage:

        # Parse project.yml for build stage
        [project, project_keys] = parse_project_keys(ctx)

        # Add waf libraries
        add_inline_libs_to_build(ctx, project, project_keys)

    Args:
        :param ctx: The WAF context
        :param project: Handle to project.yml
        :param project_keys: List of keys present in project.yml
    """

    if 'libraries' in project_keys:
        libraries_keys = project['libraries']
        if 'inline' in libraries_keys:
            if 'libraries' in project_keys:
                inlined_libs = list((project['libraries']['inline']))
                for library in inlined_libs:
                    library_keys = list(project['libraries']['inline'][library])
                    if 'build_system' in library_keys:
                        if 'waf' == project['libraries']['inline'][library]['build_system']:
                            if 'path' in library_keys:
                                library_path = project['libraries']['inline'][library]['path']
                                library_path = os.path.join(library_path, library)
                                if os.path.exists(os.path.join(library_path, 'wscript')):
                                    ctx.recurse(library_path, mandatory=True, once=True)
                            else:
                                raise Errors.ConfigurationError(
                                    error_support.BUILD_ERROR + 'Please give the ' + library + ' path')
                    else:
                        raise Errors.ConfigurationError(
                            error_support.BUILD_ERROR + 'Build system of' + library + 'is not supported')


def build_application(ctx, project, project_keys, features, appname):
    """
    The build_application builds the application using:
        ctx.env.SOURCES
        ctx.env.DEFINES
        ctx.env.INCLUDES
        ctx.env.CFLAGS
        ctx.env.USES
        ctx.env.LIBS

    Example usage:

        # Parse yml file for the build stage
        [project, project_keys] = parse_project_keys(ctx)

        # Parse the linker options of the application
        parse_and_add_linker_options(ctx, project, project_keys)

        # Parse the sources of the application
        parse_project_sources(ctx, os.path.join(ctx.path.get_bld().relpath(), 'src'), None)

        # Build the actual application
        build_application(ctx, project, project_keys)

    Args:
        :param ctx: The WAF context
        :param project: Handle to project.yml
        :param project_keys: List of keys present in project.yml
        :param features: features the build should support
    """
    # Add waf built libraries
    add_inline_libs_to_build(ctx, project, project_keys)

    if ctx.env.SOURCES:
        # Build the application
        ctx.program(
            features=features,
            source=ctx.path.ant_glob(ctx.env.SOURCES, excl=ctx.env.EXCLUDED_SOURCES),
            target=ctx.env.name + '.elf',
            defines=ctx.env.DEFINES,
            includes=ctx.env.INCLUDES,
            asflags=ctx.env.CFLAGS + ctx.env['CFLAGS_' + appname.upper()],
            cflags=ctx.env.CFLAGS + ctx.env['CFLAGS_' + appname.upper()],
            linkflags=ctx.env.EXTRA_LDFLAGS,
            use=ctx.env.USES,
            lib=ctx.env.LIBS,
            libpath=ctx.env.LIB_PATHS,
        )

        # Post build tasks
        ctx.add_post_fun(clangdb_ide_support)
        if ctx.env.platform == 'baremetal':
            ctx.add_post_fun(post_build_stats)
            ctx.add_post_fun(prepend_mss_header)
    else:
        raise Errors.ConfigurationError(error_support.BUILD_ERROR + 'No sources found')


def build_library(ctx, libname):
    """
    The build_library function builds an arbitrary library

    Example usage:

        # Parse yml file for the build stage
        [project, project_keys] = parse_project_keys(ctx)

        # Parse the linker options of the application
        parse_and_add_linker_options(ctx, project, project_keys)

        # Parse the sources of the application
        parse_project_sources(ctx, os.path.join(ctx.path.get_bld().relpath(), 'src'), None)

        # Build the actual application
        build_application(ctx, project, project_keys)

    Args:
        :param ctx: The WAF context
        :param libname: String containing the name of the library
    """
    if ctx.env['SOURCES_' + libname.upper()]:
        ctx.stlib(
            features='c cstlib',
            source=ctx.path.ant_glob(ctx.env['SOURCES_' + libname.upper()]),
            includes=ctx.env['INCLUDES_' + libname.upper()],
            cflags=ctx.env.CFLAGS + ctx.env['CFLAGS_' + libname.upper()],
            defines=ctx.env.DEFINES,
            export_includes=ctx.env['INCLUDES_' + libname.upper()],
            use=ctx.env['USES_' + libname.upper()],
            name=libname,
            target=libname.strip('lib'),
        )
    else:
        raise Errors.ConfigurationError(error_support.BUILD_ERROR + 'No sources found')
