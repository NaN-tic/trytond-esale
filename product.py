#This file is part esale module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.
from trytond.model import fields, ModelSQL
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.modules.product_esale.tools import slugify

import logging

__all__ = ['Template', 'TemplateSaleShop']
__metaclass__ = PoolMeta


class Template:
    __name__ = 'product.template'
    esale_saleshops = fields.Many2Many('product.template-sale.shop', 
            'template', 'shop', 'Websites',
            domain=[
                ('esale_available', '=', True)
            ],
            help='Select shops will be available this product')

    @staticmethod
    def default_esale_saleshops():
        Shop = Pool().get('sale.shop')
        return [p.id for p in Shop.search([('esale_available','=',True)])]

    @classmethod
    def create_esale_product(self, shop, tvals, pvals):
        '''
        Get product values and create
        :param shop: obj
        :param tvals: dict template values
        :param pvals: dict product values
        return obj
        '''
        shops = None
        Template = Pool().get('product.template')

        #Default values
        tvals['esale_available'] = True
        tvals['esale_active'] = True
        tvals['default_uom'] = shop.esale_uom_product
        tvals['category'] = shop.esale_category
        tvals['salable'] = True
        tvals['sale_uom'] = shop.esale_uom_product
        tvals['account_category'] = True
        tvals['products'] = [('create', [pvals])]
        if not tvals.get('esale_slug'):
            tvals['esale_slug'] = slugify(tvals.get('name'))

        if tvals.get('esale_saleshops'):
            shops = tvals.get('esale_saleshops')
        tvals['esale_saleshops'] = []

        template = Template.create([tvals])[0]
        Transaction().cursor.commit()
        if shops:
            Template.write([template], {'esale_saleshops': shops})
        logging.getLogger('magento sale').info(
            'Magento %s. Create product %s' % (shop.name, pvals['code']))
        return template.products[0]


class TemplateSaleShop(ModelSQL):
    'Product - Shop'
    __name__ = 'product.template-sale.shop'
    _table = 'product_template_sale_shop'
    template = fields.Many2One('product.template', 'Template', ondelete='CASCADE',
            select=True, required=True)
    shop = fields.Many2One('sale.shop', 'Shop', ondelete='RESTRICT',
            select=True, required=True)
