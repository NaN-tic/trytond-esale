# This file is part esale module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import PoolMeta

__all__ = ['ShipmentOut']


class ShipmentOut(metaclass=PoolMeta):
    __name__ = 'stock.shipment.out'

    def get_cost_invoice_line(self, invoice):
        '''Get Cost Delivery from eSale'''
        cost = None

        if hasattr(self, 'origin'):
            if self.origin:
                origin = self.origin
                if origin.__name__ == 'sale.sale':
                    if origin.esale:
                        for line in origin.lines:
                            if line.shipment_cost:
                                cost = line.unit_price # not shipment_cost
                                break

        invoice_line = super(ShipmentOut, self).get_cost_invoice_line(invoice)
        if cost:
            invoice_line.unit_price = cost
        return invoice_line
