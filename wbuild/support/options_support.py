# !/usr/bin/env python

# pylint: disable=too-many-statements, unused-argument, invalid-name, missing-class-docstring, too-few-public-methods
# -*- coding: utf-8 -*-
# Author: Francescodario Cuzzocrea <bosconovic@gmail.com>

import os


def add_common_app_options(ctx):
    """
    The add_common_app_options app_options add all those options which are common to all the applications
    built with this build system.
    The options configured trough the add_common_app_options function ARE NOT MEANT TO BE PASSED TROUGH THE USE OF
    config.yml.
    The user is ONLY allowed to override the defaults from the command line.
    For the documentation of what each option is doing, refer to the option documentation.

    Args:
        :param ctx: The WAF context

    @todo the way mpv player specify the options is more elegant https://github.com/mpv-player/mpv/blob/master/wscript
    """
    ctx.add_option('--arch',
                   action='store',
                   choices=['rv64imac', 'rv64gc'],
                   default='rv64imac',
                   help='Specify compiler architecture')
    ctx.add_option('--platform',
                   action='store',
                   choices=['baremetal', 'rtems'],
                   default='baremetal',
                   help='Specify platform on which the software will run')
    ctx.add_option('--programmer',
                   action='store',
                   choices=['openocd', 'fpgenprog'],
                   default='openocd',
                   help='Specify compiler architecture')


def add_common_library_options(ctx):
    """
    The add_common_library_options add all those options which are common to all the libraries built with this build
    system.
    The options configured trough the add_common_library_options function ARE NOT MEANT TO BE PASSED TROUGH THE USE OF
    project.yml.
    The user is ONLY allowed to override the defaults from the command line.
    For the documentation of what each option is doing, refer to the option documentation.

    @todo the way mpv player specify the options is more elegant https://github.com/mpv-player/mpv/blob/master/wscript

    Args:
        :param ctx: The WAF context
    """
    common_opt = ctx.add_option_group('Common libraries options')
    common_opt.add_option('--arch',
                          action='store',
                          choices=['rv64imac', 'rv64gc'],
                          default='rv64imac',
                          help='Specify compiler architecture')
    common_opt.add_option('--platform',
                          action='store',
                          choices=['baremetal', 'rtems'],
                          default='baremetal',
                          help='Specify platform on which the software will run')
    common_opt.add_option('--standalone',
                          action='store_true',
                          help='Build library standalone')


def parse_external_modules_options(ctx):
    """
    The parse_external_modules_options is responsible for parsing recursively the options of the external modules,
    which supports WAF as build system. if they are present.
    The path in which the application is allowed to store external modules are:

        * $application_root_dir/lib : for internally developed libraries/modules
        * $application_root_dir/ext : for third party developed libraries/modules

    The function recursively search fo wscripts in those folders and sub-folders and load into the current context the
    options exposed by the external module.

    Args:
        :param ctx: The WAF context
    """
    if os.path.exists('lib'):
        for lib_folder in os.listdir('lib'):
            module_path = os.path.join('lib', lib_folder)
            if os.path.exists(os.path.join(module_path, 'wscript')):
                ctx.recurse(module_path, mandatory=True, once=True)
