# !/usr/bin/env python

# pylint: disable=too-many-statements, unused-argument, invalid-name, missing-class-docstring, too-few-public-methods
# -*- coding: utf-8 -*-
# Author: Francescodario Cuzzocrea <bosconovic@gmail.com>

"""
Beagle-V Fore Baremetal Bootloader
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This wscript builds a baremetal bootloader for the Beagle-V Fire board
"""

import os

from wbuild.support.init_support import setup_environment
from wbuild.support.options_support import add_common_app_options
from wbuild.support.configure_support import init_app_configure_stage, parse_project_keys, setenv_from_base, configure_debug, configure_release, load_tools
from wbuild.support.build_support import parse_and_add_linker_options, parse_project_sources, build_application
from wbuild.support.distclean_support import clean_objects
from wbuild.support.load_support import program

# Those global variable are strictly needed
APPNAME = 'bvfboot'
VERSION = '0.0.0'
CODENAME = 'alpha'

top = '.'
out = 'build'


def init(ctx):
    # Run common init
    additional_targets = 'load'
    environments = 'debug release'
    setup_environment(environments, additional_targets)


def options(ctx):
    # Add common application options and parse options of external modules
    add_common_app_options(ctx)


def configure(ctx):
    # Save into WAF context the variable which are needed by the common build system
    ctx.env.name = APPNAME
    ctx.env.codename = CODENAME
    ctx.env.version = VERSION
    ctx.env.ARCH = ctx.options.arch

    # Before loading the tools (toolchain, etc...) some information need to be parsed from project.yml
    [project, project_keys] = parse_project_keys(ctx)

    # Initialize the build system
    init_app_configure_stage(ctx, project, project_keys)

    # Load appropriate tools for the arch (compiler, etc)
    load_tools(ctx)

    # Setup additional environments
    setenv_from_base(ctx, 'release', configure_release, project, project_keys, APPNAME)
    setenv_from_base(ctx, 'debug', configure_debug, project, project_keys, APPNAME)


def build(ctx):
    if ctx.variant == 'release' or ctx.variant == 'debug':
        # Parse yml file for the build stage
        [project, project_keys] = parse_project_keys(ctx)

        # Parse the linker options of the application
        parse_and_add_linker_options(ctx, project, project_keys)

        # Parse the sources of the application
        parse_project_sources(ctx, os.path.join(ctx.path.get_bld().relpath()), None)

        # Build the actual application
        build_application(ctx, project, project_keys, 'strip disassemble bin', APPNAME)

    else:
        # Waf is automatically doing a test to check whether the build variant is valid or not, so an error message
        # will be printed before this point is reached. The else condition is still put here for readability of the
        # code
        pass


def distclean(ctx):
    clean_objects()
