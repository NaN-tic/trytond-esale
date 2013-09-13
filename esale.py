#This file is part esale module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.
from trytond.model import fields, ModelSQL, ModelView
from trytond.pool import PoolMeta

__all__ = ['eSalePayment', 'eSaleStatus']
__metaclass__ = PoolMeta


class eSalePayment(ModelSQL, ModelView):
    'eSale Payment'
    __name__ = 'esale.payment'
    _rec_name = 'code'
    code = fields.Char('Code', required=True)
    payment_type = fields.Many2One('account.payment.type', 'Payment Type',
        required=True)
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
