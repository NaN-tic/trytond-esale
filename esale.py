#This file is part esale module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.
from trytond.model import fields, ModelSQL, ModelView
from trytond.pyson import Eval
from trytond.pool import PoolMeta

__all__ = ['eSaleCarrier', 'eSalePayment', 'eSaleStatus', 'eSaleSate', 'eSaleAccountTaxRule']
__metaclass__ = PoolMeta

SALE_STATES = [
    ('paid', 'Paid'),
    ('shipment', 'Delivery'),
    ('paid-shipment', 'Paid/Delivery'),
    ('cancel', 'Cancel'),
    ]


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
    confirm = fields.Boolean('Confirm',
        help='Sale change state draft to confirmed')
    cancel = fields.Boolean('Cancel',
        help='Sale change state draft to cancel.')


class eSaleSate(ModelSQL, ModelView):
    'eSale State'
    __name__ = 'esale.state'
    _rec_name = 'state'
    state = fields.Selection(SALE_STATES, 'Sale State', required=True)
    code = fields.Char('State APP Code', required=True,
        help='State APP code. Code state in your APP')
    notify = fields.Boolean('Notify',
        help='Active APP notification customer')
    shop = fields.Many2One('sale.shop', 'Sale Shop', required=True)


class eSaleAccountTaxRule(ModelSQL, ModelView):
    'eSale Tax Rule'
    __name__ = 'esale.account.tax.rule'
    _rec_name = 'tax_rule'
    country = fields.Many2One('country.country', 'Country',
        on_change=['country', 'subdivision'], required=True)
    subdivision = fields.Many2One("country.subdivision",
            'Subdivision', domain=[('country', '=', Eval('country'))],
            depends=['country'], required=True)
    start_zip = fields.Char('Start Zip', help='Numeric Zip Code')
    end_zip = fields.Char('End Zip', help='Numeric Zip Code')
    customer_tax_rule = fields.Many2One('account.tax.rule', 'Customer Tax Rule', required=True)
    supplier_tax_rule = fields.Many2One('account.tax.rule', 'Customer Tax Rule', required=True)

    def on_change_country(self):
        if (self.subdivision
                and self.subdivision.country != self.country):
            return {'subdivision': None}
        return {}
