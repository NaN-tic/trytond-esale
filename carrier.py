# This file is part esale module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from decimal import Decimal
from trytond.pool import Pool, PoolMeta
from trytond.config import config as config_

__all__ = ['Carrier']
__metaclass__ = PoolMeta

DIGITS = config_.getint('product', 'price_decimal', default=4)


class Carrier:
    __name__ = 'carrier'

    def get_sale_price_w_tax(self, price=Decimal('0.0'), party=None):
        '''
        Calculate price with taxes from carrier product
        '''
        pool = Pool()
        Tax = pool.get('account.tax')
        Invoice = pool.get('account.invoice')

        taxes = self.carrier_product.customer_taxes_used

        if taxes and party and party.customer_tax_rule:
            new_taxes = []
            for tax in taxes:
                tax_ids = party.customer_tax_rule.apply(tax, pattern={})
                new_taxes = new_taxes + tax_ids
            if new_taxes:
                taxes = Tax.browse(new_taxes)

        tax_list = Tax.compute(taxes, price, 1)
        tax_amount = Decimal('0.0')
        for tax in tax_list:
            _, val = Invoice._compute_tax(tax, 'out_invoice')
            tax_amount += val.get('amount')
        price = price + tax_amount
        price.quantize(Decimal(str(10.0 ** - DIGITS)))
        return price

    @staticmethod
    def get_products_stockable(products=[]):
        '''
        Return products are stockable
        :param products: list ids
        :return: True
        '''
        Product = Pool().get('product.product')

        prods = Product.search_read([
                ('id', 'in', products),
                ], fields_names=['type'])
        stockable = any(product['type'] in ('goods', 'assets')
            for product in prods)
        return stockable
