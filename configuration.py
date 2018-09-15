# This file is part esale module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond import backend
from trytond.model import ModelSQL, ValueMixin, fields
from trytond.pool import Pool, PoolMeta
from trytond.tools.multivalue import migrate_property

__all__ = ['Configuration', 'ConfigurationSaleEsale']
sale_delivery_product = fields.Many2One('product.product',
    'Delivery Product', domain=[
        ('salable', '=', True),
        ('type', '=', 'service'),
    ])
sale_discount_product = fields.Many2One('product.product',
    'Discount Product', domain=[
        ('salable', '=', True),
        ('type', '=', 'service'),
    ])
sale_surcharge_product = fields.Many2One('product.product',
    'Surcharge Product', domain=[
        ('salable', '=', True),
        ('type', '=', 'service'),
    ])
sale_fee_product = fields.Many2One('product.product',
    'Fee Product', domain=[
        ('salable', '=', True),
        ('type', '=', 'service'),
    ])
sale_uom_product = fields.Many2One('product.uom',
    'Default UOM')
sale_payment_type = fields.Many2One('account.payment.type',
    'Default Payment Type', domain=[
        ('kind', '=', 'receivable'),
    ])
sale_payment_term = fields.Many2One('account.invoice.payment_term',
    'Default Payment Term')
sale_currency = fields.Many2One('currency.currency',
    'Currency')
sale_account_category = fields.Many2One('product.category',
    'Account Category', domain=[
        ('accounting', '=', True),
    ])
sale_warehouse = fields.Many2One('stock.location',
    'Default Warehouse', domain=[
        ('type', '=', 'warehouse'),
    ])


class Configuration(metaclass=PoolMeta):
    __name__ = 'sale.configuration'
    sale_delivery_product = fields.MultiValue(sale_delivery_product)
    sale_discount_product = fields.MultiValue(sale_discount_product)
    sale_surcharge_product = fields.MultiValue(sale_surcharge_product)
    sale_fee_product = fields.MultiValue(sale_fee_product)
    sale_uom_product = fields.MultiValue(sale_uom_product)
    sale_payment_type = fields.MultiValue(sale_payment_type)
    sale_payment_term = fields.MultiValue(sale_payment_term)
    sale_currency = fields.MultiValue(sale_currency)
    sale_account_category = fields.MultiValue(sale_account_category)
    sale_warehouse = fields.MultiValue(sale_warehouse)

    @classmethod
    def multivalue_model(cls, field):
        pool = Pool()
        if field in {'sale_delivery_product', 'sale_discount_product',
                'sale_surcharge_product', 'sale_fee_product',
                'sale_uom_product', 'sale_payment_type', 'sale_payment_term',
                'sale_currency', 'sale_account_category', 'sale_warehouse'}:
            return pool.get('sale.configuration.esale')
        return super(Configuration, cls).multivalue_model(field)


class ConfigurationSaleEsale(ModelSQL, ValueMixin):
    "Sale Configuration Sale eSale"
    __name__ = 'sale.configuration.esale'
    sale_delivery_product = sale_delivery_product
    sale_discount_product = sale_discount_product
    sale_surcharge_product = sale_surcharge_product
    sale_fee_product = sale_fee_product
    sale_uom_product = sale_uom_product
    sale_payment_type = sale_payment_type
    sale_payment_term = sale_payment_term
    sale_currency = sale_currency
    sale_account_category = sale_account_category
    sale_warehouse = sale_warehouse

    @classmethod
    def __register__(cls, module_name):
        TableHandler = backend.get('TableHandler')
        exist = TableHandler.table_exist(cls._table)

        super(ConfigurationSaleEsale, cls).__register__(module_name)

        if not exist:
            cls._migrate_property([], [], [])

    @classmethod
    def _migrate_property(cls, field_names, value_names, fields):
        field_names.extend(['sale_delivery_product', 'sale_discount_product',
                'sale_surcharge_product', 'sale_fee_product',
                'sale_uom_product', 'sale_payment_type', 'sale_payment_term',
                'sale_currency', 'sale_account_category', 'sale_warehouse'])
        value_names.extend(['sale_delivery_product', 'sale_discount_product',
                'sale_surcharge_product', 'sale_fee_product',
                'sale_uom_product', 'sale_payment_type', 'sale_payment_term',
                'sale_currency', 'sale_account_category', 'sale_warehouse'])
        migrate_property(
            'sale.configuration', field_names, cls, value_names,
            fields=fields)
