#This file is part esale module for Tryton.
#The COPYRIGHT file at the top level of this repository contains
#the full copyright notices and license terms.
from decimal import Decimal
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.config import config
DIGITS = int(config.get('digits', 'unit_price_digits', 4))

import logging

__all__ = ['Sale', 'SaleLine']
__metaclass__ = PoolMeta


class Sale:
    __name__ = 'sale.sale'
    esale = fields.Boolean('eSale')
    reference_external = fields.Char('External Reference', readonly=True,
        select=True)
    status = fields.Char('Status', readonly=True,
        help='Last status import/export to e-commerce APP')
    status_history = fields.Text('Status history', readonly=True)

    @classmethod
    def create_external_order(cls, shop, sale_values, lines_values,
            extralines_values, party_values, invoice_values, shipment_values):
        '''
        Create external order in sale
        :param shop: obj
        :param sale_values: dict
        :param lines_values: list
        :param party_values: dict
        :param invoice_values: dict
        :param shipment_values: dict
        '''
        pool = Pool()
        Sale = pool.get('sale.sale')
        Line = pool.get('sale.line')
        Party = pool.get('party.party')
        Address = pool.get('party.address')
        eSaleCarrier = pool.get('esale.carrier')
        eSalePayment = pool.get('esale.payment')
        eSaleStatus = pool.get('esale.status')
        Currency = pool.get('currency.currency')

        sale = Sale()
        sale.shop = shop

        #Default sale values
        sale_fields = Sale.fields_get()
        for k, v in Sale.default_get(sale_fields,
                with_rec_name=False).iteritems():
            if k not in sale_values:
                sale_values[k] = v

        #Set Sale values
        sale_values['esale'] = True
        sale_values['shop'] = shop

        #Update dict from on change shop
        currency_code = sale_values.get('currency')
        sale_values.update(sale.on_change_shop())

        #Create party
        party = Party.esale_create_party(shop, party_values)
        sale.party = party

        #Create address
        invoice_address = None
        if not (invoice_values.get('street') == shipment_values.get('street')
                and invoice_values.get('zip') == shipment_values.get('zip')):
            invoice_address = Address.esale_create_address(shop, party,
                invoice_values, type='invoice')
            shipment_address = Address.esale_create_address(shop, party,
                shipment_values, type='delivery')
        else:
            shipment_address = Address.esale_create_address(shop, party,
                shipment_values)

        #Party - Address
        sale_values['party'] = party
        sale_values['invoice_address'] = invoice_address or shipment_address
        sale_values['shipment_address'] = shipment_address

        #Order reference
        if shop.esale_ext_reference:
            sale_values['reference'] = sale_values.get('reference_external')

        #Currency
        currencies = Currency.search([
                ('code', '=', currency_code),
                ], limit=1)
        if currencies:
            sale_values['currency'] = currencies[0].id
        else:
            sale_values['currency'] = shop.esale_currency.id

        #Payment
        if sale_values.get('payment'):
            payments = eSalePayment.search([
                    ('code', '=', sale_values.get('payment')),
                    ('shop', '=', shop.id),
                    ], limit=1)
            if payments:
                sale_values['payment_type'] = payments[0].payment_type
        del sale_values['payment']

        #Status
        status = eSaleStatus.search([
                ('code', '=', sale_values.get('status')),
                ('shop', '=', shop.id),
                ], limit=1)
        if status:
            sale_status = status[0]
            sale_values['invoice_method'] = sale_status.invoice_method
            sale_values['shipment_method'] = sale_status.shipment_method

        #Lines
        sale.currency = sale_values.get('currency')
        line = Line()
        line.party = party
        line.sale = sale
        lines = Line.esale_dict2lines(sale, line, lines_values)

        #Carrier + delivery line
        carriers = eSaleCarrier.search([
            ('code', '=', sale_values.get('carrier')),
            ('shop', '=', shop.id),
            ], limit=1)
        if carriers:
            carrier = carriers[0].carrier
            sale_values['carrier'] = carrier
            product_delivery = carrier.carrier_product
            shipment_description = carrier.rec_name
        else:
            del sale_values['carrier']
            product_delivery = shop.esale_delivery_product
            shipment_description = product_delivery.name
        shipment_values = [{
                'product': product_delivery.code or product_delivery.name,
                'quantity': 1,
                'description': shipment_description,
                'unit_price': sale_values.get('shipping_price', 0).quantize(
                    Decimal('.01')),
                'note': sale_values.get('shipping_note'),
                'shipment_cost': sale_values.get('shipping_price', 0).quantize(
                    Decimal('.01')),
                'sequence': 9999,
                }]
        shipment_line = Line.esale_dict2lines(sale, line, shipment_values)[0]
        # force shipment invoice on order
        sale_values['shipment_cost_method'] = 'order'
        del sale_values['shipping_price']
        del sale_values['shipping_note']

        # Surcharge
        surchage_line = None
        if (sale_values.get('surcharge') and
                sale_values.get('surcharge') != 0.0000):
            surcharge_price = Decimal(sale_values.get('surcharge', 0))
            if shop.esale_surcharge_tax_include:
                for tax in shop.esale_surcharge_product.customer_taxes_used:
                    if tax.type == 'fixed':
                        surcharge_price = surcharge_price - tax.amount
                    if tax.type == 'percentage':
                        tax_price = surcharge_price - (surcharge_price /
                            (1 + tax.rate))
                        surcharge_price = surcharge_price - tax_price
                surcharge_price.quantize(Decimal(str(10.0 ** - DIGITS)))
            surcharge_values = [{
                    'product': shop.esale_surcharge_product.code or
                            shop.esale_surcharge_product.name,
                    'quantity': 1,
                    'description': shop.esale_surcharge_product.name,
                    'unit_price': surcharge_price.quantize(Decimal('.01')),
                    'sequence': 9999,
                    }]
            surchage_line = Line.esale_dict2lines(sale, line,
                surcharge_values)[0]
            del sale_values['surcharge']

        #Discount line
        discount_line = None
        if (sale_values.get('discount') and
                sale_values.get('discount') != 0.0000):
            discount_price = Decimal(sale_values.get('discount', 0))
            if shop.esale_discount_tax_include:
                for tax in shop.esale_discount_product.customer_taxes_used:
                    if tax.type == 'fixed':
                        discount_price = discount_price - tax.amount
                    if tax.type == 'percentage':
                        tax_price = discount_price - (discount_price /
                            (1 + tax.rate))
                        discount_price = discount_price - tax_price
                discount_price.quantize(Decimal(str(10.0 ** - DIGITS)))
            discount_values = [{
                    'product': shop.esale_discount_product.code or
                            shop.esale_discount_product.name,
                    'quantity': 1,
                    'description': shop.esale_discount_product.name,
                    'unit_price': discount_price.quantize(Decimal('.01')),
                    'sequence': 9999,
                    }]
            discount_line = Line.esale_dict2lines(sale, line,
                discount_values)[0]
        del sale_values['discount']

        extralines = None
        if extralines_values:
            extralines = Line.esale_dict2lines(sale, line, extralines_values)

        #Add lines
        lines.append(shipment_line)
        if discount_line:
            lines.append(discount_line)
        if surchage_line:
            lines.append(surchage_line)
        if extralines:
            lines = [l.copy() for l in lines]
            lines = lines + extralines
        sale_values['lines'] = [('create', lines)]

        #Remove rec_name fields
        rm_fields = [val for val in sale_values if 'rec_name' in val]
        for field in rm_fields:
            del sale_values[field]

        # Create Sale
        # TODO: Add because get error when save order: could not serialize
        # access due to concurrent update
        Transaction().cursor.commit()
        with Transaction().set_context(
                company=sale_values['company'],
                without_warning=True,
                ):
            sale, = Sale.create([sale_values])
            logging.getLogger('esale').info(
                'Shop %s. Create sale %s' % (shop.name, sale.reference_external))

            if status:
                reference = sale.reference_external
                if sale_status.confirm:
                    Sale.quote([sale])
                    Sale.confirm([sale])
                    logging.getLogger('esale').info(
                        'Confirmed sale %s' % (reference))

                if sale_status.cancel:
                    Sale.cancel([sale])
                    logging.getLogger('esale').info(
                        'Canceled sale %s' % (reference))

    def set_shipment_cost(self):
        '''When sale is an esale, not recalculate shipment cost'''
        if self.esale:
            return
        return super(Sale, self).set_shipment_cost()


class SaleLine:
    __name__ = 'sale.line'

    @classmethod
    def get_shipment_line(cls, product, price, sale=None):
        '''Get shipment line
        :param product: obj
        :param price: Decimal
        return obj
        '''
        SaleLine = Pool().get('sale.line')

        shipment_line = SaleLine()
        shipment_line.sale = sale
        shipment_line.product = product
        shipment_line.description = product.rec_name
        shipment_line.quantity = 1
        shipment_line.unit = product.sale_uom
        shipment_line.unit_price = price
        shipment_line.shipment_cost = price
        shipment_line.amount = price
        shipment_line.taxes = product.customer_taxes_used
        shipment_line.sequence = 9999
        shipment_line.on_change_product()
        shipment_line.unit_price = price
        shipment_line.shipment_cost = price

        return shipment_line

    @classmethod
    def esale_dict2lines(cls, sale, line, values):
        '''
        Return list sale lines
        :param sale: obj
        :param line: obj
        :param values: dict
        return list
        '''
        Product = Pool().get('product.product')

        def default_create_product(shop, code):
            return None

        lines = []
        for l in values:
            code = l.get('product')
            products = Product.search(['OR',
                    ('name', '=', code),
                    ('code', '=', code),
                    ('codes', '=', code),
                    ], limit=1)
            if products:
                product, = products
            else:
                product_esale = getattr(Product,
                    'create_product_%s' % sale.shop.esale_shop_app,
                    default_create_product)
                product = product_esale(sale.shop, code)

            if product:
                description = l.get('description')
                l['product'] = product

                line.product = product
                line.unit = product.default_uom
                line.quantity = l['quantity']
                line.description = product.name
                product_values = line.on_change_product()

                taxes = None
                if product_values.get('taxes'):
                    taxes = product_values.get('taxes')
                if taxes:
                    l['taxes'] = [('add', taxes)]

                l['unit'] = product.default_uom
                l['description'] = description if description else product.rec_name
                for k, v in product_values.iteritems():
                    if k not in l:
                        l[k] = v

            else:
                del l['product']
                l['unit'] = sale.shop.esale_uom_product
            lines.append(l)
        return lines
