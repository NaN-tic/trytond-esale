# This file is part esale module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import fields, ModelSQL, ModelView

__all__ = ['eSaleCarrier', 'eSalePayment']


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
