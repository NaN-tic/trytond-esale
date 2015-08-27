# This file is part esale module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, fields
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta
from trytond.pyson import And, Eval, Not, Bool
from decimal import Decimal
import time
import logging

try:
    import pytz
    TIMEZONES = [(x, x) for x in pytz.common_timezones]
except ImportError:
    TIMEZONES = []
TIMEZONES += [(None, '')]

__all__ = ['SaleShop', 'SaleShopWarehouse', 'SaleShopCountry', 'SaleShopLang']
__metaclass__ = PoolMeta

logger = logging.getLogger(__name__)


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
    esale_ext_reference = fields.Boolean('External Reference',
        help='Use external reference (Increment) in sale name')
    esale_tax_include = fields.Boolean('Tax Include')
    esale_get_party_by_vat = fields.Boolean('Get Party by Vat',
        help='If there is another party with same vat, not create party')
    esale_scheduler = fields.Boolean('Scheduler',
        help='Active by crons (import/export)')
    esale_user = fields.Many2One('res.user', 'User',
        help='Use other user when user is not active (cron).')
    esale_country = fields.Many2One('country.country', 'Country',
        help='Default country related in this shop.')
    esale_countrys = fields.Many2Many('sale.shop-country.country',
        'shop', 'country', 'Countries')
    esale_delivery_product = fields.Many2One('product.product',
        'Delivery Product', domain=[
            ('salable', '=', True),
            ('type', '=', 'service'),
        ], states={
            'required': Eval('esale_available', True),
        })
    esale_discount_product = fields.Many2One('product.product',
        'Discount Product', domain=[
            ('salable', '=', True),
            ('type', '=', 'service'),
        ], states={
            'required': Eval('esale_available', True),
        })
    esale_discount_tax_include = fields.Boolean('Discount Tax Include')
    esale_surcharge_product = fields.Many2One('product.product',
        'Surcharge Product', domain=[
            ('salable', '=', True),
            ('type', '=', 'service'),
        ], states={
            'required': Eval('esale_available', True),
        })
    esale_surcharge_tax_include = fields.Boolean('Surcharge Tax Include')
    esale_fee_product = fields.Many2One('product.product',
        'Fee Product', domain=[
            ('salable', '=', True),
            ('type', '=', 'service'),
        ], states={
            'required': Eval('esale_available', True),
        })
    esale_fee_tax_include = fields.Boolean('Fee Tax Include')
    esale_uom_product = fields.Many2One('product.uom', 'Default UOM',
        states={
            'required': Eval('esale_available', True),
        },)
    esale_category = fields.Many2One('product.category', 'Default Category',
        states={
            'required': Eval('esale_available', True),
        }, help='Default Category Product when create a new product. In this '
        'category, select an Account Revenue and an Account Expense',)
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
    esale_price_party = fields.Many2One('party.party', 'Party',
        states={
            'required': And(Eval('esale_price') == 'pricelist',
                Eval('esale_available', True)),
        }, help='Select a party to compute a price from price list.')
    esale_from_orders = fields.DateTime('From Orders',
        help='This date is last import (filter)')
    esale_to_orders = fields.DateTime('To Orders',
        help='This date is to import (filter)')
    esale_last_state_orders = fields.DateTime('Last State Orders',
        help='This date is last export (filter)')
    esale_currency = fields.Many2One('currency.currency', 'Default currency',
        states={
            'required': Eval('esale_available', True),
        }, help='Default currency shop.')
    esale_carriers = fields.One2Many('esale.carrier', 'shop', 'Carriers')
    esale_payments = fields.One2Many('esale.payment', 'shop', 'Payments')
    esale_status = fields.One2Many('esale.status', 'shop', 'Status')
    esale_states = fields.One2Many('esale.state', 'shop', 'State')
    esale_timezone = fields.Selection(TIMEZONES, 'Timezone', translate=False,
        help='Select an timezone when is different than company timezone.')
    esale_import_delayed = fields.Integer('eSale Delayed Import',
        help='Total minutes delayed when import')
    esale_import_states = fields.Char('eSale Import States',
        help='If is empty, import all sales (not filter). '
            'Code states separated by comma and without space '
            '(processing,complete,...).')
    warehouses = fields.Many2Many('sale.shop-stock.location', 'shop',
        'location', 'Warehouses')

    @classmethod
    def __setup__(cls):
        super(SaleShop, cls).__setup__()
        cls._error_messages.update({
            'orders_not_import': 'Threre are not orders to import',
            'orders_not_export': 'Threre are not orders to export',
            'not_shop_user': 'Shop "%s" is not available in user preferences.',
        })
        cls._buttons.update({
                'import_orders': {},
                'export_state': {},
                })

    @staticmethod
    def default_esale_ext_reference():
        return True

    @staticmethod
    def default_esale_get_party_by_vat():
        return True

    @staticmethod
    def default_esale_price():
        return 'saleprice'

    @staticmethod
    def default_esale_log():
        return '7'

    @staticmethod
    def default_esale_lang():
        return Pool().get('res.user')(Transaction().user).language.id

    @staticmethod
    def default_esale_delivery_product():
        Config = Pool().get('sale.configuration')
        config = Config(1)
        return (config.sale_delivery_product and
            config.sale_delivery_product.id or None)

    @staticmethod
    def default_esale_discount_product():
        Config = Pool().get('sale.configuration')
        config = Config(1)
        return (config.sale_discount_product and
            config.sale_discount_product.id or None)

    @staticmethod
    def default_esale_surcharge_product():
        Config = Pool().get('sale.configuration')
        config = Config(1)
        return (config.sale_surcharge_product and
            config.sale_surcharge_product.id or None)

    @staticmethod
    def default_esale_uom_product():
        Config = Pool().get('sale.configuration')
        config = Config(1)
        return config.sale_uom_product and config.sale_uom_product.id or None

    @staticmethod
    def default_esale_import_delayed():
        return 0

    @classmethod
    def view_attributes(cls):
        return super(SaleShop, cls).view_attributes() + [
            ('//page[@id="esale"]/notebook/page[@id="actions"]', 'states', {
                    'invisible': Not(Bool(Eval('esale_available'))),
                    }),
            ('//page[@id="esale"]/notebook/page[@id="configuration"]',
                'states', {
                    'invisible': Not(Bool(Eval('esale_available'))),
                    }),
            ]

    @staticmethod
    def datetime_to_gmtime(date):
        '''
        Convert UTC timezone
        :param date: datetime
        :return str (yyyy-mm-dd hh:mm:ss)
        '''
        return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.mktime(
            time.strptime(date, "%Y-%m-%d %H:%M:%S"))))

    @staticmethod
    def datetime_to_str(date):
        '''
        Convert datetime to str
        :param date: datetime
        :return str (yyyy-mm-dd hh:mm:ss)
        '''
        return date.strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def get_shop_app(cls):
        '''Get Shop APP (magento, prestashop,...)'''
        res = [('', '')]
        return res

    def get_sales_from_date(self, date):
        '''Get Sales from a date to export
        :param date: datetime
        retun list
        '''
        pool = Pool()
        Sale = pool.get('sale.sale')
        Move = pool.get('stock.move')

        # Sale might not get updated for state changes in the related shipments
        # So first get the moves for outgoing shipments which are executed
        # after last import time.
        moves = Move.search([
            ('write_date', '>=', date),
            ('sale.shop', '=', self.id),
            ('shipment', 'like', 'stock.shipment.out%')
            ])
        sales_to_export = Sale.search(['OR', [
                    ('write_date', '>=', date),
                    ('shop', '=', self.id),
                ], [
                    ('id', 'in', map(int, [m.sale for m in moves]))
                ]])
        return sales_to_export

    def get_shop_user(self):
        '''
        Get Shop User. When user is not active, return a user
        :return user
        '''
        User = Pool().get('res.user')

        user = User(Transaction().user)
        if not user.active:
            if self.esale_user:
                user = self.esale_user
            else:
                logger.info('Add a default user in %s configuration.' % (
                    self.name))
        return user

    @classmethod
    @ModelView.button
    def import_orders(self, shops):
        """
        Import Orders from External APP
        """
        user = Pool().get('res.user')(Transaction().user)

        for shop in shops:
            if shop not in user.shops:
                logger.warning(
                    'Shop "%s" is not available in "%s" user preferences.' % (
                        shop.rec_name,
                        user.rec_name,
                        ))
                continue
            if not shop.esale_shop_app:
                continue
            with Transaction().set_context(sale_discount=False):
                import_order = getattr(shop, 'import_orders_%s' %
                    shop.esale_shop_app)
                import_order()

    @classmethod
    def import_cron_orders(cls):
        """
        Cron import orders:
        """
        shops = cls.search([
            ('esale_available', '=', True),
            ('esale_scheduler', '=', True),
            ])
        cls.import_orders(shops)
        return True

    @classmethod
    @ModelView.button
    def export_state(self, shops):
        """
        Export Orders to External APP
        """
        for shop in shops:
            export_state = getattr(shop, 'export_state_%s' %
                shop.esale_shop_app)
            export_state()

    @classmethod
    def export_cron_state(cls):
        """
        Cron export state:
        """
        shops = cls.search([
            ('esale_available', '=', True),
            ('esale_scheduler', '=', True),
            ])
        cls.export_state(shops)
        return True

    def import_orders_(self, shop):
        """Import Orders whitout app don't available
        :param shop: Obj
        """
        self.raise_user_error('orders_not_import')

    def export_state_(self, shop):
        """Export State Sale whitout app don't available
        :param shop: Obj
        """
        self.raise_user_error('orders_not_export')

    @classmethod
    def esale_price_w_taxes(cls, product, price, quantity=1):
        '''Get total price with taxes'''
        pool = Pool()
        Tax = pool.get('account.tax')
        Invoice = pool.get('account.invoice')

        # compute price with taxes
        customer_taxes = product.template.customer_taxes_used
        tax_list = Tax.compute(customer_taxes, price, quantity)
        tax_amount = Decimal('0.0')
        for tax in tax_list:
            _, val = Invoice._compute_tax(tax, 'out_invoice')
            tax_amount += val.get('amount')
        price = price + tax_amount
        return price


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
