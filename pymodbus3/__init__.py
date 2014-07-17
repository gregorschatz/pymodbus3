# -*- coding: utf-8 -*-

"""
Pymodbus3: Modbus Protocol Implementation
-----------------------------------------

TwistedModbus is built on top of the code developed by:

    Copyright (c) 2001-2005 S.W.A.C. GmbH, Germany.
    Copyright (c) 2001-2005 S.W.A.C. Bohemia s.r.o., Czech Republic.
    Hynek Petrak <hynek@swac.cz>

Released under the the BSD license
"""

from pymodbus3.version import Version
__version__ = Version.get_current_version().short()
__author__ = 'Galen Collins, Maxim Grischuk'
__author_email__ = 'bashwork@gmail.com, uzumaxy@gmail.com'

# Block unhandled logging
import logging as __logging
try:
    from logging import NullHandler as CustomNullHandler
except ImportError:
    class CustomNullHandler(__logging.Handler):
        def emit(self, record):
            pass

__logging.getLogger(__name__).addHandler(CustomNullHandler())
