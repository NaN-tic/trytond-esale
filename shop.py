#This file is part esale module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.

from trytond.model import ModelView, ModelSQL, fields
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval

import logging
import threading

__all__ = ['SaleShop', 'SaleShopCountry', 'SaleShopLang']
__metaclass__ = PoolMeta

class SaleShop:
    __name__ = 'sale.shop'

    esale_available = fields.Boolean('eSale Shop',
        states={
            'readonly': Eval('esale_available', True),
        },
        help='This is e-commerce shop.')
    esale_shop_app = fields.Selection('get_shop_app', 'Shop APP',
        states={
            'required': Eval('esale_available', True),
        }, readonly=True)
    esale_tax_include = fields.Boolean('Tax Include')
    esale_get_party_by_vat = fields.Boolean('Get Party by Vat',
        help='If there is another party with same vat, not create party')
    esale_scheduler = fields.Boolean('Scheduler',
        help='Active by crons (import/export)')
    esale_countrys = fields.Many2Many('sale.shop-country.country', 
        'shop', 'country', 'Countries')
    esale_delivery_product = fields.Many2One('product.product', 'Delivery Product',
        states={
            'required': Eval('esale_available', True),
        },
    )
    esale_discount_product = fields.Many2One('product.product', 'Discount Product',
        states={
            'required': Eval('esale_available', True),
        },
    )
    esale_uom_product = fields.Many2One('product.uom', 'Default UOM', 
        states={
            'required': Eval('esale_available', True),
        },
    )
    esale_lang = fields.Many2One('ir.lang', 'Default language',
        states={
            'required': Eval('esale_available', True),
        }, help='Default language shop. If not select, use lang user')
    esale_langs = fields.Many2Many('sale.shop-ir.lang', 
            'shop', 'lang', 'Langs')
    esale_price = fields.Selection([
            ('saleprice','Sale Price'),
            ('pricelist','Pricelist'),
    ], 'Price', states={
                'required': Eval('esale_available', True),
            },)
    esale_from_orders = fields.DateTime('From Orders', 
        help='This date is last import (filter)')
    esale_to_orders = fields.DateTime('To Orders', 
        help='This date is to import (filter)')
    esale_last_status_orders = fields.DateTime('Last Status Orders', 
        help='This date is last export (filter)')
    esale_log = fields.Selection([
        ('1','01 Day'),
        ('3','03 Days'),
        ('5','05 Days'),
        ('7','07 Days'),
        ('15','15 Days'),
        ('30','30 Days'),
        ('60','60 Days'),
        ('90','90 Days'),
    ], 'Log', help='Days from delete logs to past')
    esale_request_group = fields.Many2One('res.group', 'Group',
        states={
            'required': Eval('esale_available', True),
        }, help='Group Users to notification')

    @classmethod
    def __setup__(cls):
        super(SaleShop, cls).__setup__()
        cls._error_messages.update({
            'orders_not_import': 'Threre are not orders to import',
            'orders_not_export': 'Threre are not orders to export',
        })
        cls._buttons.update({
                'import_orders': {},
                'export_status': {},
                })

    @staticmethod
    def default_esale_price():
        return 'pricelist'

    @staticmethod
    def default_esale_log():
        return '7'

    @staticmethod
    def default_esale_lang():
        return Pool().get('res.user')(Transaction().user).language.id

    @staticmethod
    def default_esale_shop_app():
        return 'tryton'

    @classmethod
    def get_shop_app(cls):
        '''Get Shop APP (tryton, magento, prestashop,...)'''
        res = [('tryton','Tryton')]
        return res

    @classmethod
    @ModelView.button
    def import_orders(self, shops):
        """
        Import Orders from External APP
        """
        for shop in shops:
            import_order = getattr(shop, 'import_orders_%s' % shop.esale_shop_app)
            import_order(shop)

    @classmethod
    @ModelView.button
    def export_status(self, shops):
        """
        Export Orders to External APP
        """
        for shop in shops:
            export_status = getattr(shop, 'export_status_%s' % shop.esale_shop_app)
            export_status(shop)

    def import_orders_tryton(self, shop):
        """Import Orders from Tryton e-Sale don't available
        :param shop: Obj
        """
        self.raise_user_error('orders_not_import')

    def export_status_tryton(self, shop):
        """Export Status Orders to Tryton e-Sale don't available
        :param shop: Obj
        """
        self.raise_user_error('orders_not_export')


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
