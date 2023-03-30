# This file is part esale module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import ModelSQL, fields
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval, Not, Bool
from trytond.config import config as config_
from decimal import Decimal
import slug

__all__ = ['SaleShop', 'SaleShopWarehouse', 'SaleShopCountry', 'SaleShopLang']

DIGITS = config_.getint('product', 'price_decimal', default=4)


def slugify(value):
    """Convert value to slug: az09 and replace spaces by -"""
    return slug.slug(value)


class SaleShop(metaclass=PoolMeta):
    __name__ = 'sale.shop'
    esale_available = fields.Boolean('eSale Shop',
        states={
            'readonly': Eval('esale_available', True),
        },
        help='This is e-commerce shop.')
    esale_tax_include = fields.Boolean('Tax Include')
    esale_country = fields.Many2One('country.country', 'Country',
        help='Default country related in this shop.')
    esale_countrys = fields.Many2Many('sale.shop-country.country',
        'shop', 'country', 'Countries')
    esale_lang = fields.Many2One('ir.lang', 'Default language',
        states={
            'required': Eval('esale_available', True),
        }, help='Default language shop. If not select, use lang user')
    esale_langs = fields.Many2Many('sale.shop-ir.lang',
            'shop', 'lang', 'Langs')
    esale_price = fields.Selection([
            ('saleprice', 'Sale Price'),
            ('pricelist', 'Pricelist'),
            ], 'Price',
        states={
            'required': Eval('esale_available', True),
        },)
    esale_carriers = fields.One2Many('esale.carrier', 'shop', 'Carriers')
    esale_payments = fields.One2Many('esale.payment', 'shop', 'Payments')
    warehouses = fields.Many2Many('sale.shop-stock.location', 'shop',
        'location', 'Warehouses')

    @staticmethod
    def default_esale_price():
        return 'saleprice'

    @staticmethod
    def default_esale_lang():
        user = Pool().get('res.user')(Transaction().user)
        return user.language.id if user.language else None

    @classmethod
    def esale_price_w_taxes(cls, product, price, quantity=1):
        'Get total price with taxes'
        pool = Pool()
        Tax = pool.get('account.tax')
        Party = pool.get('party.party')

        # compute price with taxes
        product_customer_taxes = product.template.customer_taxes_used
        customer = Transaction().context.get('customer', None)
        customer = Party(customer) if customer else None

        party_taxes = []
        pattern = {}
        for tax in product_customer_taxes:
            if customer and customer.customer_tax_rule:
                tax_ids = customer.customer_tax_rule.apply(tax, pattern)
                if tax_ids:
                    party_taxes.extend(tax_ids)
                continue
            party_taxes.append(tax.id)
        if customer and customer.customer_tax_rule:
            tax_ids = customer.customer_tax_rule.apply(None, pattern)
            if tax_ids:
                party_taxes.extend(tax_ids)
        customer_taxes = Tax.browse(party_taxes) if party_taxes else []
        if not customer_taxes:
            customer_taxes = product_customer_taxes
        taxes = Tax.compute(customer_taxes, price, quantity)

        tax_amount = 0
        for tax in taxes:
            tax_amount += tax['amount']
        price = price + tax_amount
        return price.quantize(Decimal(str(10.0 ** - DIGITS)))

    def get_esale_payments(self, party):
        payment_types = [payment.payment_type for payment in self.esale_payments]
        default_payment_type = payment_types[0]
        if party and hasattr(party, 'customer_payment_type'):
            customer_payment = party.customer_payment_type
            if customer_payment and not customer_payment in payment_types:
                payment_types.append(customer_payment)
                default_payment_type = party.customer_payment_type
        return payment_types, default_payment_type


class SaleShopWarehouse(ModelSQL):
    'Sale Shop - Warehouse'
    __name__ = 'sale.shop-stock.location'
    _table = 'sale_shop_stock_location_rel'
    shop = fields.Many2One('sale.shop', 'Shop',
        ondelete='CASCADE', select=True, required=True)
    location = fields.Many2One('stock.location', 'Warehouse',
        ondelete='RESTRICT', select=True, required=True)


class SaleShopCountry(ModelSQL):
    'Shop - Country'
    __name__ = 'sale.shop-country.country'
    _table = 'sale_shop_country_country'

    shop = fields.Many2One('sale.shop', 'Shop', ondelete='RESTRICT',
            select=True, required=True)
    country = fields.Many2One('country.country', 'Country', ondelete='CASCADE',
            select=True, required=True)


class SaleShopLang(ModelSQL):
    'Shop - Lang'
    __name__ = 'sale.shop-ir.lang'
    _table = 'sale_shop_ir_lang'

    shop = fields.Many2One('sale.shop', 'Shop', ondelete='RESTRICT',
            select=True, required=True)
    lang = fields.Many2One('ir.lang', 'Lang', ondelete='CASCADE',
            select=True, required=True)
