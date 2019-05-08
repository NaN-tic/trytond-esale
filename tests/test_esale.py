# This file is part of the esale module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import doctest
import unittest
from decimal import Decimal
import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase, with_transaction
from trytond.tests.test_tryton import doctest_teardown, doctest_checker
from trytond.pool import Pool
from trytond.transaction import Transaction
from trytond.modules.esale.tests.tools import sale_configuration
from trytond.modules.company.tests import create_company, set_company
from trytond.modules.account.tests import create_chart
from trytond.modules.esale.tests.tools import sale_values, lines_values, \
    party_values, invoice_values, shipment_values


class EsaleTestCase(ModuleTestCase):
    'Test eSale module'
    module = 'esale'

    @with_transaction()
    def test_create_sale(self):
        pool = Pool()
        User = pool.get('res.user')
        Sequence = pool.get('ir.sequence')
        Currency = pool.get('currency.currency')
        Location = pool.get('stock.location')
        PaymentTerm = pool.get('account.invoice.payment_term')
        PriceList = pool.get('product.price_list')
        Shop = pool.get('sale.shop')
        Sale = pool.get('sale.sale')

        company = create_company()
        with set_company(company):
            create_chart(company)
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
            user = User(Transaction().user)
            user.shops = [shop]
            user.shop = shop
            user.save()

            Sale.create_external_order(shop,
                sale_values=sale_values(number='S0001'),
                lines_values=[lines_values(code='P0001')],
                party_values=party_values(),
                invoice_values=invoice_values(),
                shipment_values=shipment_values())

            sale, = Sale.search([('number', '=', 'S0001')], limit=1)
            self.assertEqual(sale.number, 'S0001')
            self.assertEqual(sale.comment, u'Example Sale Order')
            self.assertEqual(sale.total_amount, Decimal('10.00'))

            # TODO
            # - carrier
            # - payment
            # - status -> state

def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        EsaleTestCase))
    return suite
