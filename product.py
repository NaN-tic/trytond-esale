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
    esale_price = fields.Function(fields.Numeric('eSale Price',
            digits=(16, 4)), 'get_esale_price')

    @classmethod
    def get_esale_price(cls, templates, names):
        pool = Pool()
        Product = pool.get('product.product')
        User = pool.get('res.user')
        Shop = pool.get('sale.shop')

        def template_list_price():
            return {n: {t.id: t.list_price for t in templates} for n in names}

        def pricelist():
            products = [p for t in templates for p in t.products]
            sale_prices = Product.get_sale_price(products
                )
            prices = {}
            for price in sale_prices:
                for template in templates:
                    prices[template.id] = None
                    for p in template.products:
                        if (p.id == price and (
                                not prices[template.id]
                                or prices[template.id] > sale_prices[price])):
                            prices[template.id] = sale_prices[price]
            return {n: {t.id: prices[t.id] for t in templates} for n in names}

        def price_with_tax(result):
            for name in names:
                for t in templates:
                    for p in t.products:
                        result[name][t.id] = Shop.esale_price_w_taxes(p,
                            result[name][t.id])
                        break
            return result

        if (Transaction().user == 0
                and Transaction().context.get('user')):
            user = User(Transaction().context.get('user'))
        else:
            user = User(Transaction().user)
        shop = user.shop
        if not shop:
            logging.getLogger('esale').warning(
                'User %s has not any shop associated.' % (user))
            return template_list_price()
        context = {}
        if shop.esale_price == 'pricelist':
            context['price_list'] = shop.price_list.id
        if shop.price_list:
            context['customer'] = shop.esale_price_party.id
        if shop.esale_price_party:
            context['without_special_price'] = True
        with Transaction().set_context(context):
            if shop.esale_available and shop.esale_price == 'saleprice':
                result = template_list_price()
            else:
                result = pricelist()
            if shop.esale_tax_include:
                result = price_with_tax(result)
            return result

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

        template, = Template.create([tvals])
        Transaction().cursor.commit()
        if shops:
            Template.write([template], {'esale_saleshops': shops})
        product, = template.products

        logging.getLogger('esale').info(
            'Shop %s. Create product %s' % (shop.name, product.rec_name))
        return product


class TemplateSaleShop(ModelSQL):
    'Product - Shop'
    __name__ = 'product.template-sale.shop'
    _table = 'product_template_sale_shop'
    template = fields.Many2One('product.template', 'Template', ondelete='CASCADE',
            select=True, required=True)
    shop = fields.Many2One('sale.shop', 'Shop', ondelete='RESTRICT',
            select=True, required=True)
