# This file is part esale module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import datetime
from decimal import Decimal
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.pyson import Eval, Or, Not, Bool, Id
from trytond.rpc import RPC
from trytond.modules.product import price_digits
import logging

__all__ = ['Template', 'Product']

logger = logging.getLogger(__name__)


class Template(metaclass=PoolMeta):
    __name__ = 'product.template'
    esale_available = fields.Boolean('eSale',
        states={
            'readonly': Eval('esale_available', True),
            'invisible': ~Eval('salable', False),
        }, depends=['esale_available', 'salable'],
        help='This product are available in your e-commerce. '
        'If you need not publish this product (despublish), '
        'unmark Active field in eSale section.')
    esale_active = fields.Boolean('Active eSale')
    esale_price = fields.Function(fields.Numeric('eSale Price',
        digits=price_digits,
        help='eSale price is calculated from shop in user '
        'preferences and shop configuration',
        ), 'get_esale_price')
    esale_special_price = fields.Function(fields.Numeric('eSale Special Price',
        digits=price_digits,
        help='eSale special price is calculated from shop in user '
        'preferences and shop configuration',
        ), 'get_esale_special_price')
    esale_relateds_by_shop = fields.Function(fields.Many2Many(
        'product.template', None, None, 'Relateds by Shop'),
        'get_esale_relateds_by_shop')
    esale_upsells_by_shop = fields.Function(fields.Many2Many(
        'product.template', None, None, 'Upsells by Shop'),
        'get_esale_upsells_by_shop')
    esale_crosssells_by_shop = fields.Function(fields.Many2Many(
        'product.template', None, None, 'Crosssells by Shop'),
        'get_esale_crosssells_by_shop')
    esale_quantity = fields.Function(fields.Float('eSale Quantity'),
        'sum_esale_product')
    esale_forecast_quantity = fields.Function(fields.Float(
        'eSale Forecast Quantity'), 'sum_esale_product')

    @staticmethod
    def default_esale_active():
        return True

    @staticmethod
    def default_shops():
        Shop = Pool().get('sale.shop')
        return [p.id for p in Shop.search([('esale_available', '=', True)])]

    @classmethod
    def view_attributes(cls):
        return super(Template, cls).view_attributes() + [
            ('//page[@id="esale"]', 'states', {
                    'invisible': Or(Not(Bool(Eval('salable', False))),
                        ~Eval('context', {}).get('groups', []).contains(
                                Id('esale', 'group_esale'))),
                    }),
            ('//page[@id="esale"]/notebook/page[@id="general"]', 'states', {
                    'invisible': Not(Bool(Eval('esale_available'))),
                    }),
            ]

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
                for key, value in sorted(product_prices.items(),
                        key=lambda kv: (kv[1], kv[0])):
                    prices_sorted[key] = value
                prices_values = [p for p in prices_sorted.values()]
                prices[template.id] = prices_values[0] if prices_values else None
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
            logger.warning(
                'User %s has not eSale Main Shop in user preferences.' % (user)
                )
            return template_list_price()

        context = Transaction().context
        if shop.esale_price == 'pricelist':
            price_list = shop.price_list.id

            if context.get('customer'):
                customer = context['customer']
                party = Party(customer)
                if party.sale_price_list:
                    price_list = party.sale_price_list.id

            context['price_list'] = price_list

        with Transaction().set_context(context):
            result = pricelist()

            if shop.esale_tax_include:
                result = price_with_tax(result)
            return result

    @classmethod
    def get_esale_special_price(cls, templates, names):
        '''Call get_esale_price to calculate special price'''
        with Transaction().set_context(without_special_price=False):
            return cls.get_esale_price(templates, names)

    def get_esale_relateds_by_shop(self, name):
        '''Get all relateds products by shop
        (context or user shop preferences)'''
        relateds = []  # ids
        if not hasattr(self, 'esale_relateds'):
            return relateds
        if not self.esale_relateds:
            return relateds

        pool = Pool()
        transaction = Transaction()

        User = pool.get('res.user')
        SaleShop = pool.get('sale.shop')

        user = User(transaction.user)
        if Transaction().context.get('shop'):
            shop = SaleShop(transaction.context.get('shop'))
        else:
            shop = user.shop
        if not shop:
            return relateds

        for template in self.esale_relateds:
            if shop in template.shops:
                relateds.append(template.id)
        return relateds

    def get_esale_upsells_by_shop(self, name):
        '''Get all upsells products by shop
        (context or user shop preferences)'''
        upsells = []  # ids
        if not hasattr(self, 'esale_upsells'):
            return upsells
        if not self.esale_upsells:
            return upsells

        pool = Pool()
        transaction = Transaction()

        User = pool.get('res.user')
        SaleShop = pool.get('sale.shop')

        user = User(transaction.user)
        if Transaction().context.get('shop'):
            shop = SaleShop(transaction.context.get('shop'))
        else:
            shop = user.shop
        if not shop:
            return upsells

        for template in self.esale_upsells:
            if shop in template.shops:
                upsells.append(template.id)
        return upsells

    def get_esale_crosssells_by_shop(self, name):
        '''Get all crosssells products by shop
        (context or user shop preferences)'''
        crosssells = []  # ids
        if not hasattr(self, 'esale_crosssells'):
            return crosssells
        if not self.esale_crosssells:
            return crosssells

        pool = Pool()
        transaction = Transaction()

        User = pool.get('res.user')
        SaleShop = pool.get('sale.shop')

        user = User(transaction.user)
        if Transaction().context.get('shop'):
            shop = SaleShop(transaction.context.get('shop'))
        else:
            shop = user.shop
        if not shop:
            return crosssells

        for template in self.esale_crosssells:
            if shop in template.shops:
                crosssells.append(template.id)
        return crosssells

    def sum_esale_product(self, name):
        if name not in ('esale_quantity', 'esale_forecast_quantity'):
            raise Exception('Bad argument')
        sum_ = 0.
        for product in self.products:
            sum_ += getattr(product, name)
        return sum_

    @classmethod
    def create_esale_product(cls, shop, vals):
        '''
        Create a product from eSale dict values
        :param shop: obj
        :param vals: dict product values (template + products)
        return obj
        '''

        # Default values
        vals['default_uom'] = shop.esale_uom_product
        vals['salable'] = True
        vals['sale_uom'] = shop.esale_uom_product
        vals['account_category'] = shop.esale_account_category
        vals['accounts_category'] = True

        template, = cls.create([vals])
        Transaction().commit()
        product, = template.products

        logger.info('Shop %s. Create product %s' % (
            shop.name, product.rec_name))
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


class Product(metaclass=PoolMeta):
    __name__ = 'product.product'
    esale_quantity = fields.Function(fields.Float('eSale Quantity'),
        'get_esale_quantity')
    esale_forecast_quantity = fields.Function(fields.Float(
        'eSale Forecast Quantity'), 'get_esale_quantity')

    @classmethod
    def __setup__(cls):
        super(Product, cls).__setup__()
        cls.__rpc__.update({
                'get_esale_product_quantity': RPC(),
                })

    @staticmethod
    def get_esale_product_quantity(codes, name='quantity'):
        '''Get eSale Product Quantity
        @param codes: list codes
        @param type: quantity or forecast_quantity
        '''
        pool = Pool()
        Product = pool.get('product.product')
        ProductCode = pool.get('product.code')

        products = []
        for code in codes:
            prods = Product.search(['OR',
                    ('name', '=', code),
                    ('code', '=', code),
                    ], limit=1)
            if prods:
                prod, = prods
            else:
                product_codes = ProductCode.search([
                        ('number', '=', code)
                        ], limit=1)
                if product_codes:
                    prod = product_codes[0].product
                else:
                    continue
            products.append(prod)

        qties = Product.get_esale_quantity(products, name)
        return [{'id': p.id, 'code': p.code, 'qty': qties[p.id] or 0.0}
                for p in products if p.id in qties]

    @classmethod
    def get_esale_quantity(cls, products, name):
        Date = Pool().get('ir.date')

        transaction = Transaction()
        context = transaction.context
        shop_id = context.get('shop', None)

        locations = []
        if shop_id:
            shop = Pool().get('sale.shop')(shop_id)

            # storage and input location in warehouse
            if shop.warehouses:
                for w in shop.warehouses:
                    locations.append(w.storage_location.id)
                    locations.append(w.input_location.id)
            elif shop.warehouse:
                locations.append(shop.warehouse.storage_location.id)
                locations.append(shop.warehouse.input_location.id)
        context['locations'] = locations

        if name[6:] == 'forecast_quantity':
            context['forecast'] = True
            context['stock_date_end'] = datetime.date.max
        else:
            context['forecast'] = False
            context['stock_date_end'] = Date.today()
        context['stock_assign'] = True
        context['with_childs'] = True

        with transaction.set_context(context):
            return cls.get_quantity(products, name[6:])

    @staticmethod
    def esale_product_values():
        '''Default values Product Product'''
        return {}
