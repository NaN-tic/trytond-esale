# This file is part esale module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import logging
import stdnum.eu.vat as vat
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval

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

    @classmethod
    def esale_create_party(self, shop, values):
        '''
        Create Party
        :param shop: obj
        :param values: dict
        return party object
        '''
        pool = Pool()
        Party = pool.get('party.party')
        Identifier = pool.get('party.identifier')
        ContactMechanism = pool.get('party.contact_mechanism')

        vat_code = values.get('vat_code')
        vat_country = values.get('vat_country')

        is_vat = False
        if vat_country and vat_code:
            code = '%s%s' % (vat_country.upper(), vat_code)
            if vat.is_valid(code):
                vat_code = code
                is_vat = True

        #  Search party by:
        #  - VAT country + VAT code
        #  - VAT code
        #  - Party eSale Email
        #  - Party Email

        # search by VAT
        if shop.esale_get_party_by_vat and vat_code:
            parties = Party.search([
                ('identifier_code', '=', vat_code),
                ], limit=1)
            if not parties and is_vat:
                parties = Party.search([
                    ('identifier_code', '=', vat_code[2:]),
                    ], limit=1)
            if parties:
                party, = parties
                return party

        # search by esale email
        if values.get('esale_email'):
            parties = Party.search([
                ('esale_email', '=', values.get('esale_email')),
                ], limit=1)
            if parties:
                party, = parties
                return party

            # search by mechanism email
            mechanisms = ContactMechanism.search([
                ('type', '=', 'email'),
                ('value', '=', values.get('esale_email')),
                ], limit=1)
            if mechanisms:
                mechanism, = mechanisms
                return mechanism.party

        # not found, create
        party = Party()
        for k, v in values.items():
            if k not in _ESALE_PARTY_EXCLUDE_FIELDS:
                setattr(party, k, v)
        party.addresses = None
        if vat_code:
            identifier = Identifier()
            identifier.code = vat_code
            identifier.type = 'eu_vat' if is_vat else None
            party.identifiers = [identifier]
        party.save()
        logger.info('Shop %s. Created party ID %s' % (
            shop.name, party.id))
        return party


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

            # calculate subdivision/city from zip+country
            # TODO support get subdivision from dict values
            # At the moment, get subdivision from zip + country
            if values.get('subdivision') == '':
                del values['subdivision']
            if values.get('zip') and values.get('country'):
                address = Address()
                address.zip = values.get('zip')
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
                    [cm._save_values for cm in contact_mechanisms])
        return address
