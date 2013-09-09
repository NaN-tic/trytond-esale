#This file is part esale module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction

__all__ = ['Sale']
__metaclass__ = PoolMeta


class Sale:
    'Sale'
    __name__ = 'sale.sale'
    reference_external = fields.Char('External Reference', readonly=True, select=True)
    status_history_external = fields.Text('Status history', readonly=True)

    @classmethod
    def create_external_order(self, shop, sale_values, lines_values, party_values, 
                        invoice_values, shipment_values):
        '''
        Create external order in sale
        :param shop: obj
        :param salev: dict
        :param linesv: list
        :param partyv: dict
        :param invoicev: dict
        :param shipmentv: dict
        '''
        pool = Pool()
        Sale = pool.get('sale.sale')
        Line = pool.get('sale.line')
        Party = pool.get('party.party')
        Address = pool.get('party.address')

        #Order reference
        if shop.esale_ext_reference:
            sale_values['reference'] = sale_values.get('reference_external')

        party = Party.esale_create_party(shop, party_values)

        if not ((invoice_values.get('street') == shipment_values.get('street')) and \
                (invoice_values.get('zip') == shipment_values.get('zip'))):
            invoice_address = Address.esale_create_address(shop, party, 
                invoice_values, type='invoice')
            shipment_address = Address.esale_create_address(shop, party,
                shipment_values, type='delivery')
        else:
            shipment_address = Address.esale_create_address(shop, party,
                shipment_values)

