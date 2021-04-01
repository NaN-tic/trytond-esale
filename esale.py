# This file is part esale module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import fields, ModelSQL, ModelView, MatchMixin
from trytond.pool import Pool
from trytond.pyson import Eval
from trytond import backend


class eSaleCarrier(ModelSQL, ModelView):
    'eSale Carrier'
    __name__ = 'esale.carrier'
    _rec_name = 'code'
    code = fields.Char('Code', required=True)
    carrier = fields.Many2One('carrier', 'Carrier', required=True)
    shop = fields.Many2One('sale.shop', 'Sale Shop', required=True)


class eSalePayment(ModelSQL, ModelView):
    'eSale Payment'
    __name__ = 'esale.payment'
    _rec_name = 'code'
    code = fields.Char('Code', required=True)
    payment_type = fields.Many2One('account.payment.type', 'Payment Type',
        domain=[('kind', '=', 'receivable')], required=True)
    shop = fields.Many2One('sale.shop', 'Sale Shop', required=True)
    sequence = fields.Integer('Sequence', required=True)

    @classmethod
    def __setup__(cls):
        super(eSalePayment, cls).__setup__()
        cls._order.insert(0, ('sequence', 'ASC'))
        cls._order.insert(1, ('id', 'ASC'))

    @staticmethod
    def default_sequence():
        return 1


class eSaleStatus(ModelSQL, ModelView):
    'eSale Status'
    __name__ = 'esale.status'
    _rec_name = 'code'
    code = fields.Char('Code', required=True)
    shop = fields.Many2One('sale.shop', 'Sale Shop', required=True)
    invoice_method = fields.Selection([
            ('manual', 'Manual'),
            ('order', 'On Order Processed'),
            ('shipment', 'On Shipment Sent')
            ], 'Sale Invoice Method', required=True)
    shipment_method = fields.Selection([
            ('manual', 'Manual'),
            ('order', 'On Order Processed'),
            ('invoice', 'On Invoice Paid'),
            ], 'Sale Shipment Method', required=True)
    quote = fields.Boolean('Quote',
        help='Sale change state draft to quotation')
    confirm = fields.Boolean('Confirm',
        help='Sale change state quotation to confirmed')
    process = fields.Boolean('Process',
        help='Sale change state confirmed to processing')
    cancel = fields.Boolean('Cancel',
        help='Sale change state draft to cancel')

    @staticmethod
    def default_invoice_method():
        return 'order'

    @staticmethod
    def default_shipment_method():
        return 'order'


class eSaleSate(ModelSQL, ModelView):
    'eSale State'
    __name__ = 'esale.state'
    _rec_name = 'code'
    state = fields.Selection([], 'Sale State', required=True)
    code = fields.Char('State APP Code', required=True,
        help='State APP code. Code state in your APP')
    notify = fields.Boolean('Notify',
        help='Active APP notification customer')
    shop = fields.Many2One('sale.shop', 'Sale Shop', required=True)
    message = fields.Text('Message', translate=True)
    cancel = fields.Boolean('Cancel')

    @classmethod
    def __setup__(cls):
        Sale = Pool().get('sale.sale')
        super(eSaleSate, cls).__setup__()
        states = Sale.state.selection
        for state in [
                    ('paid', 'Paid'),
                    ('shipment', 'Delivery'),
                    ('paid-shipment', 'Paid/Delivery'),
                    ]:
            if state not in states:
                states.append(state)
        cls.state.selection = states


class eSaleAccountTaxRule(ModelSQL, ModelView, MatchMixin):
    'eSale Tax Rule'
    __name__ = 'esale.account.tax.rule'
    country = fields.Many2One('country.country', 'Country',
        required=True)
    subdivision = fields.Many2One("country.subdivision",
            'Subdivision', domain=[('country', '=', Eval('country'))],
            depends=['country'])
    postal_code = fields.Char('Postal Code')
    customer_tax_rule = fields.Many2One('account.tax.rule',
        'Customer Tax Rule', required=True)
    supplier_tax_rule = fields.Many2One('account.tax.rule',
        'Supplier Tax Rule', required=True)
    sequence = fields.Integer('Sequence')

    @classmethod
    def __setup__(cls):
        super(eSaleAccountTaxRule, cls).__setup__()
        cls._order.insert(0, ('sequence', 'ASC'))

    @classmethod
    def __register__(cls, module_name):
        table = backend.TableHandler(cls, module_name)

        if table.column_exist('start_zip'):
            table.column_rename('start_zip', 'zip')

        # Migration from 5.8: rename country_zip to location
        table.column_rename('zip', 'postal_code')

        super().__register__(module_name)

    @staticmethod
    def default_sequence():
        return 1

    def get_rec_name(self, name):
        return self.customer_tax_rule.name

    @fields.depends('country', 'subdivision')
    def on_change_country(self):
        if not self.country:
            self.subdivision = None

    @classmethod
    def compute(cls, country, subdivision=None, postal_code=None, pattern=None):
        'Compute esale account tax rule based on party address'
        domain = [('country', '=', country)]
        etax_rules = cls.search(domain, order=[('sequence', 'ASC')])
        if pattern is None:
            pattern = {}

        pattern = pattern.copy()
        pattern['country'] = country and country.id or None
        if subdivision:
            pattern['subdivision'] = subdivision.id
        if postal_code:
            pattern['postal_code'] = postal_code

        for etax_rule in etax_rules:
            if etax_rule.match(pattern):
                return etax_rule
        return
