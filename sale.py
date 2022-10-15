# This file is part esale module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import fields
from trytond.pyson import Eval
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
import logging

__all__ = ['Sale']

logger = logging.getLogger(__name__)
_ESALE_SALE_EXCLUDE_FIELDS = ['shipping_price', 'shipping_note', 'discount',
    'discount_description', 'coupon_code', 'coupon_description', 'carrier',
    'currency', 'payment']


class Sale(metaclass=PoolMeta):
    __name__ = 'sale.sale'
    esale = fields.Boolean('eSale',
        states={
            'readonly': Eval('state') != 'draft',
            },
        depends=['state'])
    carrier_tracking_ref = fields.Function(fields.Char('Carrier Tracking Ref'),
        'get_carrier_tracking_ref')
    number_packages = fields.Function(fields.Integer('Number of Packages'),
        'get_number_packages')

    @classmethod
    def copy(cls, sales, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default['esale'] = False
        return super(Sale, cls).copy(sales, default=default)

    @classmethod
    def view_attributes(cls):
        return super(Sale, cls).view_attributes() + [
            ('//page[@id="esale"]', 'states', {
                    'invisible': ~Eval('esale'),
                    }),
            ]

    def set_shipment_cost(self):
        # not set shipment cost when sale is generated from eSale
        if self.esale:
            return []
        return super(Sale, self).set_shipment_cost()

    def get_shipment_cost_line(self, carrier, cost, unit_price=None):
        Line = Pool().get('sale.line')

        cost_line = super(Sale, self).get_shipment_cost_line(carrier, cost, unit_price)

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
