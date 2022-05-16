
# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from trytond.modules.sale_shop.tests import SaleShopCompanyTestMixin
from trytond.tests.test_tryton import ModuleTestCase


class EsaleTestCase(SaleShopCompanyTestMixin, ModuleTestCase):
    'Test Esale module'
    module = 'esale'
    extras = ['sale_discount', 'sale_pos', 'sale_stock_quantity', 'stock_delivery']


del ModuleTestCase
