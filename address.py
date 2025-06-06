# This file is part esale module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool, PoolMeta
import logging

logger = logging.getLogger(__name__)


class Address(metaclass=PoolMeta):
    __name__ = 'party.address'

    @classmethod
    def esale_create_address(self, shop, party, values, type=None):
        '''
        Create Party Address
        :param shop: obj
        :param party: obj
        :param values: dict
        return party object
        '''
        pool = Pool()
        Address = pool.get('party.address')
        ContactMechanism = pool.get('party.contact_mechanism')
        Country = pool.get('country.country')

        # Country
        country = values.get('country')
        if country and not isinstance(country, int):
            countries = Country.search(['OR',
                ('name', 'like', country),
                ('code', '=', country.upper()),
                ], limit=1)
            if countries:
                country, = countries
                values['country'] = country
            else:
                del values['country']
        elif 'country' in values and not country:
            del values['country']

        # Address
        postal_code = values.get('postal_code')
        addresses = Address.search([
            ('party', '=', party),
            ('street', '=', values.get('street')),
            ('postal_code', '=', postal_code),
            ], limit=1)
        if addresses:
            address = addresses[0]

            invoice = None
            delivery = None
            if(type == 'invoice' and not address.invoice):
                invoice = True
            if(type == 'delivery' and not address.delivery):
                delivery = True
            if(invoice or delivery):
                Address.write([address], {
                    'delivery': delivery,
                    'invoice': invoice,
                    })
        else:
            cmechanisms = []
            if values.get('phone'):
                cmechanisms.append(
                    {'type': 'phone', 'value': values['phone']})
            if values.get('email'):
                cmechanisms.append(
                    {'type': 'email', 'value': values['email']})
            if values.get('fax'):
                cmechanisms.append(
                    {'type': 'fax', 'value': values['fax']})

            if 'phone' in values:
                del values['phone']
            if 'email' in values:
                del values['email']
            if 'fax' in values:
                del values['fax']

            values['party'] = party
            if not type:
                values['delivery'] = True
                values['invoice'] = True
            if type == 'invoice':
                values['invoice'] = True
            if type == 'delivery':
                values['delivery'] = True

            # calculate subdivision/city from postal_code+country
            # TODO support get subdivision from dict values
            # At the moment, get subdivision from postal_code + country
            if values.get('subdivision') == '':
                del values['subdivision']
            if values.get('postal_code') and values.get('country'):
                address = Address()
                address.postal_code = values.get('postal_code')
                address.country = values.get('country')

            if values.get('name') and not values.get('party_name'):
                values['party_name'] = values['name']
                del values['name']

            address, = Address.create([values])
            logger.info('Shop %s. Create address ID %s' % (
                shop.name, address.id))

            contact_mechanisms = []
            for contact in cmechanisms:
                cmechanism = ContactMechanism()
                cmechanism.party = party
                cmechanism.type = contact['type']
                cmechanism.value = contact['value']
                cmechanism.on_change_value()
                contact_mechanisms.append(cmechanism)
            if contact_mechanisms:
                ContactMechanism.create(
                    [cm._save_values() for cm in contact_mechanisms])
        return address
