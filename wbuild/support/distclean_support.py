# !/usr/bin/env python
# pylint: disable=too-many-statements, unused-argument, invalid-name, missing-class-docstring, too-few-public-methods
# -*- coding: utf-8 -*-
# Author: Francescodario Cuzzocrea <bosconovic@gmail.com>

import shutil


def clean_objects() -> None:
    # The clean_objects function can be used to remove all the objects generated in
    # the build directory.

    shutil.rmtree('build', ignore_errors=True)
    shutil.rmtree('build_current', ignore_errors=True)
