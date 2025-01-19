# !/usr/bin/env python

# pylint: disable=too-many-statements, unused-argument, invalid-name, missing-class-docstring, too-few-public-methods, line-too-long
# -*- coding: utf-8 -*-
# Author: Francescodario Cuzzocrea <bosconovic@gmail.com>

import yaml
import os
import shutil

from wbuild.support.common_support import post_build_stats, prepend_mss_header


def _parse_linker_options(ctx, project, project_keys) -> None:
    # The parse_linker_options parses the board linker options from project.yml.
    # It requires as an argument the handle to the project.yml and the list of keys extrapulated
    # from project.yml. In particular, it sets up the linker script
    # to be used by the application and sets the libraries linking order if requested.
    #
    # The parse_linker_options is a private function, and it is not meant to be called outside
    # this module.
    #
    # Args:
    #     :param ctx: The WAF context
    #     :param project: Handle to project.yml
    #     :param project_keys: List of keys present in project.yml

    if 'linker' not in project_keys:
        return

    linker_keys = project['linker']

    ld_script = linker_keys.get('script')
    if ld_script:
        ctx.env.ld_script = ld_script
    else:
        ctx.fatal('Please declare at least the linker script in the linker field.')

    link_order = linker_keys.get('order')
    if link_order:
        ctx.env.LIBS = tuple(link_order)


def _add_linker_options(ctx) -> None:
    # The add_linker_options add all the relevant linkflags to the ctx.env.LINKFLAGS
    # global variable.
    # In particular, it also let you select the desired linker script according to the
    # ctx.env.ld_script global variable.
    #
    # The add_linker_options is a private function, and it is not meant to be called outside
    # this module.
    #
    # Args:
    #     :param ctx: The WAF context
    #

    # Initial population of target arch
    link_flags = ['-mcmodel=medany']
    if ctx.env.ARCH == 'rv64imac':
        link_flags.extend(['-march=rv64imac_zicsr_zifencei', '-mabi=lp64'])
    elif ctx.env.ARCH == 'rv64imafdc':
        link_flags.extend(['-march=rv64imafdc_zicsr_zifencei', '-mabi=lp64d'])
    else:
        ctx.fatal(f'{ctx.env.ARCH} is not supported. Currently supported archs are rv64imac and rv64imafdc')

    # Always generate MAP file and perform dead code elimination
    link_flags.extend([f'-Wl,-Map={ctx.env.name}.map', '-Wl,--gc-sections'])

    # Append linker script path to LDFLAGS if not using default one
    if ctx.env.ld_script:
        link_flags.extend([
            f'-L{os.path.join(ctx.path.bldpath(), "confs", "linker")}',
            f'-T{ctx.env.ld_script}.ld'
        ])

    if ctx.env.platform == 'baremetal':
        link_flags.extend(['-nostartfiles', '--specs=nano.specs'])

    elif ctx.env.platform == 'rtems':
        rtems_bsp_root = os.environ.get('RTEMSBSPROOT')
        if rtems_bsp_root:
            arch_path = ctx.env.ARCH.replace('rv', 'mpfs')
            link_flags.extend([
                f'-B{os.path.join(rtems_bsp_root, arch_path, "lib")}',
                '-qrtems'
            ])
        else:
            ctx.fatal('RTEMSBSPROOT environment variable not set.')

    ctx.env.append_unique('EXTRA_LDFLAGS', link_flags)


def parse_and_add_linker_options(ctx, project, project_keys) -> None:
    # The parse_and_add_linker_options parses the board linker options from project.yml.
    # It requires as an argument the handle to the project.yml and the list of keys extrapulated
    # from project.yml. In particular, it sets up the linker script to be used by the application
    # and sets the libraries linking order if requested.
    # If you are enforcing linking order, remember to add the lib=ctx.env.LIBS variable to
    # your application ctx.program.
    # The function then configures the linker script to be used.
    #
    # Example snippet of project.yml:
    #
    #     linker:
    #       script: lim
    #       order:
    #         - goofy
    #         - daisy
    #         - donald
    #
    # Args:
    #     :param ctx: The WAF context
    #     :param project: Handle to project.yml
    #     :param project_keys: List of keys present in project.yml

    _parse_linker_options(ctx, project, project_keys)
    _add_linker_options(ctx)


def _file_existance_check(ctx, sources_list) -> None:
    # This function is used to check if the source files declared in project.yml
    # exist in the current path. If not, it raises a fatal error.
    #
    # Args:
    #     :param ctx: The WAF context
    #     :param list: The list of source files to check

    for file in sources_list:
        if not os.path.isfile(file):
            ctx.fatal(f'Source file {file} does not exist')


def parse_project_sources(ctx, path, name) -> None:
    # The parse_project_sources function appends the list of source files and the
    # include paths found in the provided sources.yml.
    # The function is also recursive, this means that if your provide a module entry
    # in project.yml, it will enter into the supplied module folder, parse the sources.yml
    # and append it to the list of includes and sources of the parent.
    #
    # In the case the function is called by an application, the name argument must be set
    # to None, while in the case the function is called by a library, the name argument
    # must be set to libname.
    #
    # For example:
    #
    #   - app:
    #       parse_project_sources(ctx, os.path.join(ctx.path.get_bld().relpath(), 'src'), None)
    #
    #   - library:
    #       parse_project_sources(ctx, ctx.path.get_bld().relpath(), LIBNAME.upper())
    #
    # where LIBNAME = libpippo
    #
    # Args:
    #     :param ctx: The WAF context
    #     :param path: Path to sources.yml
    #     :param name: Optional argument, name. To be set to None in case of the caller is an app,
    #                  otherwise to libname in case the caller is a library.

    if not os.path.exists(os.path.join(path, 'sources.yml')):
        ctx.fatal(f'{path} does not contain any sources.yml')

    with open(os.path.join(path, 'sources.yml'), encoding='utf-8') as f:
        srcs=yaml.safe_load(f)
        for key, value in srcs.items():
            if key == 'includes':
                includes_var = f'INCLUDES_{name}' if name else 'INCLUDES'
                ctx.env.append_unique(includes_var, value)
            elif key == 'files':
                # In here we are building the full source file path relative to the directory
                # were the top level wscript has been called. This is needed for the file
                # existance check, which check that all the source files are effectively
                # present in the file system
                full_file_paths = [os.path.normpath(os.path.join(path, file))
                                    for file in srcs['files']]
                _file_existance_check(ctx, full_file_paths)
                # In here we need to remove from the path the portion of path which is
                # relative to the directory containing the top level wscript. This is
                # needed when we inline libraries into the build of an application
                rel_file_paths = [os.path.normpath(
                    os.path.join(os.path.relpath(path, ctx.path.get_src().relpath()), file))
                                    for file in srcs['files']]
                sources_var = f'SOURCES_{name}' if name else 'SOURCES'
                ctx.env.append_unique(sources_var, rel_file_paths)
            elif key == 'modules':
                app_modules = value
                for module in app_modules:
                    if os.path.exists(os.path.join(path, module)):
                        parse_project_sources(ctx, os.path.join(path, module), name)
                    else:
                        ctx.fatal(f'{os.path.join(path, module)} does not contain any sources.yml')


def _add_inline_libs_to_build(ctx, project, project_keys) -> None:
    # The add_inline_libs_to_build recurse trough each WAF inline library
    # added to the project and recursively calls the build functions present
    # in the respective wscripts, building the target libraries.
    #
    # Example usage:
    #
    #     # Parse project.yml for build stage
    #     [project, project_keys] = parse_project_keys(ctx)
    #
    #     # Add waf libraries
    #     add_inline_libs_to_build(ctx, project, project_keys)
    #
    # Args:
    #     :param ctx: The WAF context
    #     :param project: Handle to project.yml
    #     :param project_keys: List of keys present in project.yml

    libraries = project.get('libraries', {})
    inlined_libs = libraries.get('inline', {})

    if 'libraries' in project_keys and inlined_libs:
        for library, library_data in inlined_libs.items():
            build_system = library_data.get('build_system')
            library_path = library_data.get('path')

            if build_system != 'waf':
                ctx.fatal(f'Build system of {library} is not supported')
                continue

            if not library_path:
                ctx.fatal(f'Please give the {library} path')
                continue

            library_full_path = os.path.join(library_path, library)
            wscript_path = os.path.join(library_full_path, 'wscript')

            if os.path.exists(wscript_path):
                ctx.recurse(library_full_path, mandatory=True, once=True)
            else:
                ctx.fatal(f'wscript not found for {library} at {library_full_path}')


def _clangdb_ide_support(ctx) -> None:
    # The clangdb_ide_support simply copies the compile_commands.json file
    # into the project root directory for usage by the IDEs which are supporting clangdb
    #
    # Example usage:
    #
    #     # Post built tasks
    #     ctx.add_post_fun(clangdb_ide_support)
    #
    # Args:
    #     :param ctx: The WAF context

    shutil.copy(os.path.join(ctx.variant_dir, 'compile_commands.json'),
                ctx.path.get_bld().relpath())


def build_application(ctx, project, project_keys, features, appname) -> None:
    # Builds the application using the provided context and project 
    # configuration:
    #
    #     ctx.env.SOURCES
    #     ctx.env.DEFINES
    #     ctx.env.INCLUDES
    #     ctx.env.CFLAGS
    #     ctx.env.USES
    #     ctx.env.LIBS
    #
    # Example usage:
    #
    #     # Parse yml file for the build stage
    #     [project, project_keys] = parse_project_keys(ctx)
    #
    #     # Parse the linker options of the application
    #     parse_and_add_linker_options(ctx, project, project_keys)
    #
    #     # Parse the sources of the application
    #     parse_project_sources(ctx, os.path.join(ctx.path.get_bld().relpath(), 'src'), None)
    #
    #     # Build the actual application
    #     build_application(ctx, project, project_keys)
    #
    # Args:
    #     :param ctx: The WAF context
    #     :param project: Handle to project.yml
    #     :param project_keys: List of keys present in project.yml
    #     :param features: features the build should support

    def _add_app_post_build_tasks():
        # Adds the necessary post-build tasks based on the environment
        # and options.
        ctx.add_post_fun(_clangdb_ide_support)
        ctx.add_post_fun(post_build_stats)

        if ctx.env.platform in ('baremetal', 'rtems'):
            if ctx.env.is_bootloader == 'true':
                ctx.add_post_fun(prepend_mss_header)

    if 'libraries' in project_keys:
        # Add waf built libraries
        _add_inline_libs_to_build(ctx, project, project_keys)

    if ctx.env.SOURCES:
        # Build the application
        ctx.program(
            features=features,
            source=ctx.path.ant_glob(ctx.env.SOURCES, excl=ctx.env.EXCLUDED_SOURCES),
            target=f'{ctx.env.name}.elf',
            defines=ctx.env.DEFINES,
            includes=ctx.env.INCLUDES,
            cflags=ctx.env[f'CFLAGS_{appname.upper()}'],
            linkflags=ctx.env.EXTRA_LDFLAGS,
            use=ctx.env.USES,
            lib=ctx.env.LIBS,
            libpath=ctx.env.LIB_PATHS,
        )

        # Post build tasks
        _add_app_post_build_tasks()
    else:
        ctx.fatal('No sources found.')


def build_library(ctx, libname) -> None:
    # The build_library function builds an arbitrary library
    #
    # Example usage:
    #
    #     # Parse yml file for the build stage
    #     [project, project_keys] = parse_project_keys(ctx)
    #
    #     # Parse the linker options of the application
    #     parse_and_add_linker_options(ctx, project, project_keys)
    #
    #     # Parse the sources of the application
    #     parse_project_sources(ctx, os.path.join(ctx.path.get_bld().relpath(), 'src'), None)
    #
    #     # Build the actual application
    #     build_application(ctx, project, project_keys)
    #
    # Args:
    #     :param ctx: The WAF context
    #     :param libname: String containing the name of the library

    def _add_standalone_lib_post_build_tasks():
        ctx.add_post_fun(_clangdb_ide_support)

    if ctx.env[f'SOURCES_{libname.upper()}']:
        ctx.stlib(
            features='c cstlib',
            source=ctx.path.ant_glob(ctx.env[f'SOURCES_{libname.upper()}']),
            includes=ctx.env[f'INCLUDES_{libname.upper()}'],
            cflags=ctx.env.CFLAGS + ctx.env[f'CFLAGS_{libname.upper()}'],
            defines=ctx.env.DEFINES,
            export_includes=ctx.env[f'INCLUDES_{libname.upper()}'],
            use=ctx.env[f'USES_{libname.upper()}'],
            name=libname,
            target=libname.strip('lib'),
        )

        if ctx.options.standalone:
            # Post build tasks
            _add_standalone_lib_post_build_tasks()
    else:
        ctx.fatal('No sources found.')
