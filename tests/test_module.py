
# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from trytond.modules.company.tests import CompanyTestMixin
from trytond.tests.test_tryton import ModuleTestCase


class EsaleTestCase(CompanyTestMixin, ModuleTestCase):
    'Test Esale module'
    module = 'esale'


del ModuleTestCase
