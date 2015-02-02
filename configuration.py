#This file is part esale module for Tryton.
#The COPYRIGHT file at the top level of this repository contains
#the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta

__all__ = ['Configuration']
__metaclass__ = PoolMeta


class Configuration:
    __name__ = 'sale.configuration'
    sale_delivery_product = fields.Property(fields.Many2One('product.product',
        'Delivery Product', domain=[('salable', '=', True)], required=True))
    sale_discount_product = fields.Property(fields.Many2One('product.product',
        'Discount Product', domain=[('salable', '=', True)], required=True))
    sale_surcharge_product = fields.Property(fields.Many2One('product.product',
        'Surcharge Product', domain=[('salable', '=', True)], required=True))
    sale_uom_product = fields.Property(fields.Many2One('product.uom',
        'Default UOM', required=True))
    sale_warehouse = fields.Property(fields.Many2One('stock.location',
        'Default Warehouse', domain=[('type', '=', 'warehouse')],
        required=True))
    sale_payment_type = fields.Property(fields.Many2One('account.payment.type',
        'Default Payment Type', domain=[('kind', '=', 'receivable')],
        required=True))
    sale_payment_term = fields.Property(
        fields.Many2One('account.invoice.payment_term',
        'Default Payment Term', required=True))
    sale_price_list = fields.Property(fields.Many2One('product.price_list',
        'Default Price List', required=True))
    sale_currency = fields.Property(fields.Many2One('currency.currency',
        'Currency', required=True))
    sale_category = fields.Property(fields.Many2One('product.category',
        'Product Category', required=True))
