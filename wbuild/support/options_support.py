# !/usr/bin/env python

# pylint: disable=too-many-statements, unused-argument, invalid-name, missing-class-docstring, too-few-public-methods, line-too-long
# -*- coding: utf-8 -*-
# Author: Francescodario Cuzzocrea <bosconovic@gmail.com>

import os


def add_common_app_options(ctx) -> None:
    # The add_common_app_options app_options add all those options which are common to all the
    # applications built with this build system.
    # The options configured trough the add_common_app_options function
    # ARE NOT MEANT TO BE PASSED TROUGH THE USE OF project.yml.
    # The user is ONLY allowed to override the defaults from the command line.
    # For the documentation of what each option is doing, refer to the option documentation.
    #
    # Args:
    #     :param ctx: The WAF context
    #

    common_app_opt = ctx.add_option_group('Common application options')
    common_app_opt.add_option('--arch',
                              action='store',
                              choices=['rv64imac', 'rv64imafdc', 'x86_64'],
                              default='rv64imac',
                              help='Specify compiler architecture')
    common_app_opt.add_option('--hw-version',
                              action='store',
                              choices=['ICICLE', 'CORE3-BB', 'CORE3-EM'],
                              default='ICICLE',
                              help='Specify the hardware version of the board. Icicle stands for '
                                   'Icicle Dev-Kit, while CORE3 stands for internal CORE3 board')
    common_app_opt.add_option('--program',
                              action='store',
                              choices=['openocd', 'fpgenprog'],
                              default='openocd',
                              help='Specify how to program the board')
    common_app_opt.add_option('--is-bootloader',
                              action='store_true',
                              default='false',
                              help='Wether this application is bootloader or not')
    add_envm_programming_options(ctx)


def add_envm_programming_options(ctx) -> None:
    # The add_envm_programming_options add all those options which are common to all the
    # software which needs to be flashet to the eNVM memory of the Polarfir SoC and are
    # built using this build system.
    # The options configured trough the add_envm_programming_options function
    # ARE NOT MEANT TO BE PASSED TROUGH THE USE OF project.yml.
    # The user is ONLY allowed to override the defaults from the command line.
    # For the documentation of what each option is doing, refer to the option documentation.
    #
    # Args:
    #     :param ctx: The WAF context

    envm_prg_opt = ctx.add_option_group('eNVM programming options')
    envm_prg_opt.add_option('--target-package',
                            action='store',
                            choices=['FCVG484', 'FCSG536'],
                            default='FCVG484',
                            help='Package of the Polarfire SoC')


def add_common_library_options(ctx) -> None:
    # The add_common_library_options add all those options which are common to all the
    # libraries built with this build system.
    # The options configured trough the add_common_library_options function
    # ARE NOT MEANT TO BE PASSED TROUGH THE USE OF project.yml.
    # The user is ONLY allowed to override the defaults from the command line.
    # For the documentation of what each option is doing, refer to the option documentation.
    #
    # Args:
    #     :param ctx: The WAF context

    common_lib_opt = ctx.add_option_group('Common libraries options. Valid for standalone library compilation')
    common_lib_opt.add_option('--arch',
                              action='store',
                              choices=['rv64imac', 'rv64imafdc', 'x86_64'],
                              default='rv64imac',
                              help='Specify compiler architecture')
    common_lib_opt.add_option('--standalone', action='store_true',
                              help='Build library standalone')
    common_lib_opt.add_option('--platform',
                              action='store',
                              choices=['baremetal', 'rtems', 'linux'],
                              default='baremetal',
                              help='Specify platform on which the software will run')


    # The parse_external_modules_options is responsible for parsing recursively
    # the options of the external modules, which supports WAF as build system. if they are present.
    # The path in which the application is allowed to store external modules are:
    #
    #     * $application_root_dir/lib : for internally developed libraries/modules
    #     * $application_root_dir/ext : for third party developed libraries/modules
    #
    # The function recursively search fo wscripts in those folders and
    # sub-folders and load into the current context the options exposed by the external module.
    #
    # Args:
    #     :param ctx: The WAF context

    def _recurse_wscript_in_folder(folder):
        # Recursively checks for wscripts in the specified folder and subfolders
        # and loads them into the current context.
        #
        # Args:
        #     folder: The directory to search for wscripts.
        if os.path.exists(folder):
            for lib_folder in os.listdir(folder):
                module_path = os.path.join(folder, lib_folder)
                if os.path.exists(os.path.join(module_path, 'wscript')):
                    ctx.recurse(module_path, mandatory=True, once=True)

    _recurse_wscript_in_folder('lib')
    _recurse_wscript_in_folder('ext')
