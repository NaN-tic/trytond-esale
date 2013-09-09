#This file is part esale module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta

__all__ = ['Sale']
__metaclass__ = PoolMeta


class Sale:
    'Sale'
    __name__ = 'sale.sale'
    reference_external = fields.Char('External Reference', readonly=True, select=True)
    status_history_external = fields.Text('Status history', readonly=True)

    def create_external_order(self, values):
        '''
        Create external order in sale
        '''
        print "aqui"
