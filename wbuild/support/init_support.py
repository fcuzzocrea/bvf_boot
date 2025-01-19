# !/usr/bin/env python

# pylint: disable=too-many-statements, unused-argument, invalid-name, missing-class-docstring, too-few-public-methods
# -*- coding: utf-8 -*-
# Author: Francescodario Cuzzocrea <bosconovic@gmail.com>

from waflib.Build import BuildContext, CleanContext
from waflib.extras.clang_compilation_database import ClangDbContext


def setup_environment(environments, additional_targets) -> None:
    # The setup_env function is responsible for setting up the debug and release environment
    # for applications (or libraries) build. It must be called during the init stage of the
    # application (or library) wscript.
    # By default, configures debug and release environment for the build and clean target.
    # Additional target which might be needed by the particular application can be passed as
    # argument to the function itself.
    # If the application does not want to set debug and release environment for special target,
    # the additional_target argument must be set to None.
    #
    # Args:
    #     :param additional_targets: List containing the additional target for which the application
    #                                needs to generate debug and release environment

    # Create debug and release configuration
    for x in environments.split():
        for y in (BuildContext, CleanContext, ClangDbContext):
            name = y.__name__.replace('Context', '').lower()
            class tmp(y):
                cmd = name + '_' + x
                variant = x

    # Create debug and release configuration for
    # our custom targets if necessary
    if additional_targets is not None:
        for x in environments.split():
            for y in additional_targets:
                class tmp(BuildContext):
                    cmd = y + '_' + x
                    fun = y
                    variant = x

    # Default to release if no configuration is passed
    for y in (BuildContext, ClangDbContext):
        class tmp(y):
            variant = 'release'
