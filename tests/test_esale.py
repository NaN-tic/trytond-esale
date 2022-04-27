# This file is part of the esale module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import unittest
from decimal import Decimal
import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase, with_transaction
from trytond.pool import Pool
from trytond.transaction import Transaction
from trytond.modules.company.tests import create_company, set_company
from trytond.modules.company.tests import CompanyTestMixin


class EsaleTestCase(CompanyTestMixin, ModuleTestCase):
    'Test eSale module'
    module = 'esale'


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        EsaleTestCase))
    return suite
