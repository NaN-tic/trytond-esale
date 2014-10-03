#This file is part esale module for Tryton.
#The COPYRIGHT file at the top level of this repository contains
#the full copyright notices and license terms.
from trytond.pool import Pool, PoolMeta

import logging

__all__ = ['Address']
__metaclass__ = PoolMeta


class Address:
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
        if not isinstance(country, int):
            countries = Country.search(['OR',
                ('name', 'like', country),
                ('code', '=', country.upper()),
                ], limit=1)
            if countries:
                country, = countries
                values['country'] = country
            else:
                del values['country']

        # Address
        zip = values.get('zip')
        addresses = Address.search([
            ('party', '=', party),
            ('street', '=', values.get('street')),
            ('zip', '=', zip),
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
            address_contacts = []
            if values.get('phone'):
                address_contacts.append(
                    {'type': 'phone', 'value': values['phone']})
            if values.get('email'):
                address_contacts.append(
                    {'type': 'email', 'value': values['email']})
            if values.get('fax'):
                address_contacts.append(
                    {'type': 'fax', 'value': values['fax']})

            del values['phone']
            del values['email']
            del values['fax']

            values['party'] = party
            if not type:
                values['delivery'] = True
                values['invoice'] = True

            address, = Address.create([values])
            logging.getLogger('eSale').info(
                'Shop %s. Create address ID %s' % (shop.name, address.id))

            for contact in address_contacts:
                ContactMechanism.create([{
                    'party': party,
                    'address': address,
                    'type': contact['type'],
                    'value': contact['value'],
                    }])
        return address
