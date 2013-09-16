#This file is part esale module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.
from trytond.model import fields, ModelSQL
from trytond.pool import PoolMeta
from trytond.pyson import Eval

__all__ = ['Template', 'TemplateSaleShop']
__metaclass__ = PoolMeta


class Template:
    "Product Template"
    __name__ = 'product.template'
    esale_available = fields.Boolean('Available eSale',
            states={
                'readonly': Eval('esale_available', True),
            },
            help='This product are available in your e-commerce. ' \
            'If you need not publish this product (despublish), ' \
            'unmark Active field in eSale section.')
    esale_active = fields.Boolean('Active',
            help='If check this, this product can shop it')
    esale_saleshops = fields.Many2Many('product.template-sale.shop', 
            'template', 'shop', 'Websites',
            domain=[
                ('esale_available', '=', True)
            ],
            help='Select shops will be available this product')


class TemplateSaleShop(ModelSQL):
    'Product - Shop'
    __name__ = 'product.template-sale.shop'
    _table = 'product_template_sale_shop'
    template = fields.Many2One('product.template', 'Template', ondelete='CASCADE',
            select=True, required=True)
    shop = fields.Many2One('sale.shop', 'Shop', ondelete='RESTRICT',
            select=True, required=True)
