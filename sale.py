# This file is part esale module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from decimal import Decimal
from trytond import backend
from trytond.model import fields, Unique
from trytond.pyson import Eval
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.config import config as config_
import logging

__all__ = ['Sale', 'SaleLine', 'Cron']

DIGITS = config_.getint('product', 'price_decimal', default=4)
PRECISION = Decimal(str(10.0 ** - DIGITS))
logger = logging.getLogger(__name__)
_ESALE_SALE_EXCLUDE_FIELDS = ['shipping_price', 'shipping_note', 'discount',
    'discount_description', 'coupon_code', 'coupon_description', 'carrier',
    'currency', 'payment']


class Cron(metaclass=PoolMeta):
    __name__ = 'ir.cron'

    @classmethod
    def __setup__(cls):
        super(Cron, cls).__setup__()
        cls.method.selection.extend([
            ('sale.shop|import_cron_orders', "eSale - Import Sales"),
            ('sale.shop|export_cron_state', "eSale - Export State"),
        ])


class Sale(metaclass=PoolMeta):
    __name__ = 'sale.sale'
    esale = fields.Boolean('eSale',
        states={
            'readonly': Eval('state') != 'draft',
            },
        depends=['state'])
    number_external = fields.Char('External Number', readonly=True,
        select=True)
    esale_coupon = fields.Char('eSale Coupon', readonly=True)
    status = fields.Char('eSale Status', readonly=True,
        help='Last status import/export to e-commerce APP')
    status_history = fields.Text('eSale Status history', readonly=True)
    carrier_tracking_ref = fields.Function(fields.Char('Carrier Tracking Ref'),
        'get_carrier_tracking_ref')
    number_packages = fields.Function(fields.Integer('Number of Packages'),
        'get_number_packages')

    @classmethod
    def __register__(cls, module_name):
        TableHandler = backend.get('TableHandler')

        table = TableHandler(cls, module_name)

        # Migration from 3.8: rename reference_external into number_external
        if (table.column_exist('reference_external')
                and not table.column_exist('number_external')):
            table.drop_constraint('reference_external_uniq')
            table.column_rename('reference_external', 'number_external')

        super(Sale, cls).__register__(module_name)

        # Migration from 5.4: remove number_external_uniq
        table.drop_constraint('number_external_uniq')

    @classmethod
    def copy(cls, sales, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default['number_external'] = None
        return super(Sale, cls).copy(sales, default=default)

    @classmethod
    def view_attributes(cls):
        return super(Sale, cls).view_attributes() + [
            ('//page[@id="esale"]', 'states', {
                    'invisible': ~Eval('esale'),
                    }),
            ('//page[@id="esale"]/group[@id="external_price"]', 'states', {
                    'invisible': ~Eval('external_untaxed_amount'),
                    }),
            ]

    def set_shipment_cost(self):
        # not set shipment cost when sale is generated from eSale
        if self.esale:
            return []
        return super(Sale, self).set_shipment_cost()

    def get_shipment_cost_line(self, cost):
        Line = Pool().get('sale.line')

        cost_line = super(Sale, self).get_shipment_cost_line(cost)

        sale_fields = Line._fields.keys()
        # add default values in cost line
        default_values = Line.default_get(sale_fields, with_rec_name=False)
        for k in default_values:
            if not hasattr(cost_line, k):
                setattr(cost_line, k, default_values[k])
        # add all sale line fields in cost line
        for k in sale_fields:
            if not hasattr(cost_line, k):
                setattr(cost_line, k, None)
        return cost_line

    def get_carrier_tracking_ref(self, name):
        refs = []
        for shipment in self.shipments:
            if not hasattr(shipment, 'carrier_tracking_ref'):
                return
            if shipment.carrier_tracking_ref:
                refs.append(shipment.carrier_tracking_ref)
        if refs:
            return ','.join(refs)

    def get_number_packages(self, name):
        packages = 0
        for shipment in self.shipments:
            if not hasattr(shipment, 'number_packages'):
                return
            if shipment.number_packages:
                packages += shipment.number_packages
        return packages

    @classmethod
    def _check_stock_quantity(cls, sales):
        # Not check stock quantity (user warning) according the context
        if not Transaction().context.get('without_warning', False):
            super(Sale, cls)._check_stock_quantity(sales)

    def esale_sale_export_csv(self):
        vals = {}
        if self.shop.esale_ext_reference:
            number = self.reference_external or self.number
        else:
            number = self.number
        vals['number'] = number
        vals['state'] = self.state
        return vals
