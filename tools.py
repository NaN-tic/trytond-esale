# encoding: utf-8
# This file is part esale module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.

def is_a_vat(vat):
    # When a vat is required, users add some characters like
    # '-', '_', '--', '.', ...
    # This method try to skip those vats
    # http://ec.europa.eu/taxation_customs/vies/faq.html
    if not len(vat) >= 2: # RO vat minimum of 2 characters
        return False
    return any(char.isdigit() for char in vat)
