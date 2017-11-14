# This file is part of the esale module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import unittest
import doctest
from decimal import Decimal
import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase
from trytond.tests.test_tryton import POOL, DB_NAME, USER, CONTEXT
from trytond.transaction import Transaction
from trytond.modules.esale.tests.tools import sale_configuration
from trytond.modules.esale.tests.tools import sale_values, lines_values, \
    party_values, invoice_values, shipment_values

class EsaleTestCase(ModuleTestCase):
    'Test eSale module'
    module = 'esale'

    def test010create_sale(self):
        User = POOL.get('res.user')
        Sequence = POOL.get('ir.sequence')
        Currency = POOL.get('currency.currency')
        Location = POOL.get('stock.location')
        PaymentTerm = POOL.get('account.invoice.payment_term')
        PriceList = POOL.get('product.price_list')
        Shop = POOL.get('sale.shop')
        Sale = POOL.get('sale.sale')

        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            # update sale configuration
            sale_configuration()

            payment_term, = PaymentTerm.search([], limit=1)
            product_price_list, = PriceList.search([], limit=1)
            warehouse, = Location.search([('type', '=', 'warehouse')], limit=1)
            currency, = Currency.search([], limit=1)
            sequence, = Sequence.search([('code', '=', 'sale.sale')], limit=1)

            shop = Shop()
            shop.name = 'Shop test'
            shop.warehouse = warehouse
            shop.currency = currency
            shop.sale_sequence = sequence
            shop.price_list = product_price_list
            shop.payment_term = payment_term
            shop.sale_invoice_method = 'shipment'
            shop.sale_shipment_method = 'order'
            shop.esale_ext_reference = True
            shop.save()

            # set user shop
            user = User(USER)
            user.shops = [shop]
            user.shop = shop
            user.save()

            Sale.create_external_order(shop,
                sale_values=sale_values(reference='S0001'),
                lines_values=[lines_values(code='P0001')],
                party_values=party_values(),
                invoice_values=invoice_values(),
                shipment_values=shipment_values())

            sale, = Sale.search([('reference', '=', 'S0001')], limit=1)
            self.assertEqual(sale.reference, 'S0001')
            self.assertEqual(sale.comment, u'Example Sale Order')
            self.assertEqual(sale.total_amount, Decimal('10.00'))

            # discount new line
            sale_data = sale_values(reference='S0002')
            sale_data['discount'] = Decimal('-6')

            Sale.create_external_order(shop,
                sale_values=sale_data,
                lines_values=[lines_values(code='P0001')],
                party_values=party_values(),
                invoice_values=invoice_values(),
                shipment_values=shipment_values())

            sale, = Sale.search([('reference', '=', 'S0002')], limit=1)
            self.assertEqual(sale.total_amount, Decimal('4.00'))
            self.assertEqual(len(sale.lines), 2)

            # TODO
            # - carrier
            # - payment
            # - status -> state

def suite():
    suite = trytond.tests.test_tryton.suite()
    from trytond.modules.company.tests import test_company
    for test in test_company.suite():
        if test not in suite and not isinstance(test, doctest.DocTestCase):
            suite.addTest(test)
    from trytond.modules.account.tests import test_account
    for test in test_account.suite():
        if test not in suite and not isinstance(test, doctest.DocTestCase):
            suite.addTest(test)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        EsaleTestCase))
    return suite
