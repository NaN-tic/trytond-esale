# This file is part esale module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta
from trytond.pyson import Eval
import logging

logger = logging.getLogger(__name__)
_ESALE_PARTY_EXCLUDE_FIELDS = ['vat_country', 'vat_code']


class Party(metaclass=PoolMeta):
    __name__ = 'party.party'
    esale_email = fields.Char('E-Mail')

    @classmethod
    def view_attributes(cls):
        return super(Party, cls).view_attributes() + [
            ('//page[@id="esale"]', 'states', {
                    'invisible': ~Eval('esale_email'),
                    })]
