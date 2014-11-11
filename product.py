#This file is part esale module for Tryton.
#The COPYRIGHT file at the top level of this repository contains
#the full copyright notices and license terms.
from decimal import Decimal
from trytond.model import fields, ModelSQL
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.modules.product_esale.tools import slugify
from trytond.config import CONFIG
DIGITS = int(CONFIG.get('unit_price_digits', 4))

import logging

__all__ = ['Template', 'Product', 'TemplateSaleShop']
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
            digits=(16, DIGITS),
            help='eSale price is calculated from shop in user '
                'preferences and shop configuration',
            ), 'get_esale_price')
    esale_special_price = fields.Function(fields.Numeric('eSale Special Price',
            digits=(16, DIGITS),
            help='eSale special price is calculated from shop in user '
                'preferences and shop configuration',
            ), 'get_esale_special_price')

    @classmethod
    def get_esale_price(cls, templates, names):
        pool = Pool()
        Product = pool.get('product.product')
        User = pool.get('res.user')
        Shop = pool.get('sale.shop')
        Party = pool.get('party.party')

        def template_list_price():
            return {n: {t.id: t.list_price for t in templates} for n in names}

        def pricelist():
            '''
            Get prices from all products by sale price list
            From all products, return price cheaper
            '''
            products = [p for t in templates for p in t.products]
            if not products:
                return {
                        n: {t.id: Decimal(0) for t in templates} for n in names
                    }

            # get all product prices
            sale_prices = Product.get_sale_price(products)

            prices = {}
            for template in templates:
                products = [p.id for p in template.products]
                if not products:
                    prices[template.id] = Decimal(0.0)
                    continue

                product_prices = {}
                for product in products:
                    product_prices[product] = sale_prices[product]

                prices_sorted = {}
                for key, value in sorted(product_prices.iteritems(),
                        key=lambda (k, v): (v, k)):
                    prices_sorted[key] = value

                # get cheaper price
                prices[template.id] = prices_sorted.values()[0]
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
        if not shop or not shop.esale_available:
            logging.getLogger('esale').warning(
                'User %s has not eSale Main Shop in user preferences.' % (user)
                )
            return template_list_price()

        context = Transaction().context
        if shop.esale_price == 'pricelist':
            customer = shop.esale_price_party.id
            price_list = shop.price_list.id

            if context.get('customer'):
                customer = context['customer']
                party = Party(customer)
                if party.sale_price_list:
                    price_list = party.sale_price_list.id

            context['customer'] = customer
            context['price_list'] = price_list

        with Transaction().set_context(context):
            if shop.esale_price == 'saleprice':
                result = template_list_price()
            else:
                result = pricelist()
            if shop.esale_tax_include:
                result = price_with_tax(result)
            return result

    @classmethod
    def get_esale_special_price(cls, templates, names):
        '''Call get_esale_price to calculate special price (configuration shop)'''
        with Transaction().set_context(without_special_price=False):
            return cls.get_esale_price(templates, names)

    @staticmethod
    def default_esale_saleshops():
        Shop = Pool().get('sale.shop')
        return [p.id for p in Shop.search([('esale_available', '=', True)])]

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

    @staticmethod
    def esale_template_values():
        '''Default values Product Template'''
        tvals = {}
        tvals['esale_available'] = True
        tvals['esale_active'] = True
        tvals['salable'] = True
        tvals['account_category'] = True
        tvals['type'] = 'goods'
        return tvals


class Product:
    __name__ = 'product.product'
    
    @staticmethod
    def esale_product_values():
        '''Default values Product Product'''
        return {}


class TemplateSaleShop(ModelSQL):
    'Product - Shop'
    __name__ = 'product.template-sale.shop'
    _table = 'product_template_sale_shop'
    template = fields.Many2One('product.template', 'Template',
        ondelete='CASCADE', select=True, required=True)
    shop = fields.Many2One('sale.shop', 'Shop', ondelete='RESTRICT',
        select=True, required=True)
