#This file is part esale module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta

__all__ = ['Configuration']
__metaclass__ = PoolMeta


class Configuration:
    'Sale Configuration'
    __name__ = 'sale.configuration'
    sale_delivery_product = fields.Many2One('product.product', 'Delivery Product', 
        required=True)
    sale_discount_product = fields.Many2One('product.product', 'Discount Product',
        required=True)
    sale_uom_product = fields.Many2One('product.uom', 'Default UOM',
        required=True)
    sale_request_group = fields.Many2One('res.group', 'Default Group Users',
        required=True)
