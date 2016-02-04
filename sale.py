# This file is part esale module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from decimal import Decimal
from trytond.model import fields, Unique
from trytond.pyson import Eval
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.config import config as config_
import logging

__all__ = ['Sale', 'SaleLine']
__metaclass__ = PoolMeta

DIGITS = config_.getint('product', 'price_decimal', default=4)
PRECISION = Decimal(str(10.0 ** - DIGITS))
logger = logging.getLogger(__name__)
_ESALE_SALE_EXCLUDE_FIELDS = ['shipping_price', 'shipping_note', 'discount',
    'discount_description', 'coupon_code', 'coupon_description', 'carrier',
    'currency', 'payment']


class Sale:
    __name__ = 'sale.sale'
    esale = fields.Boolean('eSale',
        states={
            'readonly': Eval('state') != 'draft',
            },
        depends=['state'])
    reference_external = fields.Char('External Reference', readonly=True,
        select=True)
    esale_coupon = fields.Char('eSale Coupon', readonly=True)
    status = fields.Char('eSale Status', readonly=True,
        help='Last status import/export to e-commerce APP')
    status_history = fields.Text('eSale Status history', readonly=True)

    @classmethod
    def __setup__(cls):
        super(Sale, cls).__setup__()
        t = cls.__table__()
        cls._sql_constraints.extend([
            ('reference_external_uniq', Unique(t, t.shop, t.reference_external),
             'There is another sale with the same reference external.\n'
             'The reference external of the sale must be unique!')
        ])

    @classmethod
    def copy(cls, sales, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default['reference_external'] = None
        return super(Sale, cls).copy(sales, default=default)

    @classmethod
    def view_attributes(cls):
        return super(Sale, cls).view_attributes() + [
            ('//page[@id="esale"]', 'states', {
                    'invisible': ~Eval('esale'),
                    }),
            ('//page[@id="esale"]/group[@id="external_price"]', 'states', {
                    'invisible': ~Eval('external_untaxed_amount'),
                    }),
            ]

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

        # Create party
        party = Party.esale_create_party(shop, party_values)

        sale = Sale.get_sale_data(party)
        for k, v in sale_values.iteritems():
            if k not in _ESALE_SALE_EXCLUDE_FIELDS:
                setattr(sale, k, v)
        sale.shop = shop # force shop; not user context
        sale.esale = True

        # Create address
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
        sale.invoice_address = invoice_address or shipment_address
        sale.shipment_address = shipment_address

        # Order reference
        if shop.esale_ext_reference:
            sale.reference = sale_values.get('reference_external')

        # Currency
        currencies = Currency.search([
                ('code', '=', sale_values.get('currency')),
                ], limit=1)
        if currencies:
            currency, = currencies
            sale.currency = currency
        else:
            currency = shop.esale_currency
            sale.currency = currency

        # Payment Type
        if sale_values.get('payment'):
            payments = eSalePayment.search([
                    ('code', '=', sale_values.get('payment')),
                    ('shop', '=', shop.id),
                    ], limit=1)
            if payments:
                sale.payment_type = payments[0].payment_type

        # Status
        status = eSaleStatus.search([
                ('code', '=', sale_values.get('status')),
                ('shop', '=', shop.id),
                ], limit=1)
        if status:
            sale_status, = status
            sale.invoice_method = sale_status.invoice_method
            sale.shipment_method = sale_status.shipment_method

        # Lines
        lines = Line.esale_dict2lines(sale, lines_values)

        # Carrier + delivery line
        carriers = eSaleCarrier.search([
            ('code', '=', sale_values.get('carrier')),
            ('shop', '=', shop.id),
            ], limit=1)
        if carriers:
            carrier = carriers[0].carrier
            sale.carrier = carrier
            product_delivery = carrier.carrier_product
            shipment_description = carrier.rec_name
        else:
            product_delivery = shop.esale_delivery_product
            shipment_description = product_delivery.name
        shipment_values = [{
                'product': product_delivery.code or product_delivery.name,
                'quantity': 1,
                'unit_price': sale_values.get('shipping_price', 0).quantize(PRECISION),
                'description': shipment_description,
                'note': sale_values.get('shipping_note'),
                'sequence': 9999,
                }]
        shipment_line, = Line.esale_dict2lines(sale, shipment_values)
        shipment_line.shipment_cost = sale_values.get('shipping_price', 0).quantize(
                    Decimal(str(10.0 ** -currency.digits)))
        sale.shipment_cost_method = 'order' # force shipment invoice on order

        # Fee - Payment service
        fee_line = None
        if (sale_values.get('fee') and
                sale_values.get('fee') != 0.0000):
            fee_price = Decimal(sale_values.get('fee', 0))
            if shop.esale_fee_tax_include:
                for tax in shop.esale_fee_product.customer_taxes_used:
                    if tax.type == 'fixed':
                        fee_price = fee_price - tax.amount
                    if tax.type == 'percentage':
                        tax_price = fee_price - (fee_price /
                            (1 + tax.rate))
                        fee_price = fee_price - tax_price
                fee_price.quantize(PRECISION)
            fee_values = [{
                    'product': shop.esale_fee_product.code or
                        shop.esale_fee_product.name,
                    'quantity': 1,
                    'unit_price': fee_price.quantize(PRECISION),
                    'description': shop.esale_fee_product.rec_name,
                    'sequence': 9999,
                    }]
            fee_line, = Line.esale_dict2lines(sale, fee_values)

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
                surcharge_price.quantize(PRECISION)
            surcharge_values = [{
                    'product': shop.esale_surcharge_product.code or
                            shop.esale_surcharge_product.name,
                    'quantity': 1,
                    'unit_price': surcharge_price.quantize(PRECISION),
                    'description': shop.esale_surcharge_product.rec_name,
                    'sequence': 9999,
                    }]
            surchage_line, = Line.esale_dict2lines(sale, surcharge_values)

        # Discount line
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
                discount_price.quantize(PRECISION)

            description = shop.esale_discount_product.name
            if sale_values.get('discount_description'):
                description = sale_values.get('discount_description')
            if sale_values.get('coupon_code'):
                description += ' (%s)' % sale_values.get('coupon_code')

            if (sale_values.get('coupon_description') and
                    sale_values.get('coupon_code')):
                sale_values['esale_coupon'] = '[%s] %s' % (
                    sale_values['coupon_code'],
                    sale_values['coupon_description'])
            elif sale_values.get('coupon_code'):
                sale_values['esale_coupon'] = '%s' % (
                    sale_values['coupon_code'])

            discount_values = [{
                    'product': shop.esale_discount_product.code or
                            shop.esale_discount_product.name,
                    'quantity': 1,
                    'unit_price': discount_price.quantize(PRECISION),
                    'description': description,
                    'sequence': 9999,
                    }]
            discount_line, = Line.esale_dict2lines(sale, discount_values)

        extralines = None
        if extralines_values:
            extralines = Line.esale_dict2lines(sale, extralines_values)

        # Add lines
        lines.append(shipment_line)
        if discount_line:
            lines.append(discount_line)
        if fee_line:
            lines.append(fee_line)
        if surchage_line:
            lines.append(surchage_line)
        if extralines:
            lines = lines + extralines
        sale.lines = lines

        # Create Sale
        with Transaction().set_context(
                without_warning=True,
                ):
            sale.save()
            logger.info('Shop %s. Saved sale %s' % (
                shop.name, sale.reference_external))

            if status:
                reference = sale.reference_external
                if sale_status.process and not sale_status.confirm:
                    Sale.quote([sale])
                    logger.info('Quotation sale %s' % (reference))
                if sale_status.confirm:
                    Sale.quote([sale])
                    Sale.confirm([sale])
                    logger.info('Confirmed sale %s' % (reference))
                if sale_status.cancel:
                    Sale.cancel([sale])
                    logger.info('Canceled sale %s' % (reference))
        Transaction().cursor.commit()

    def set_shipment_cost(self):
        '''When sale is an esale, not recalculate shipment cost'''
        if self.esale:
            return
        return super(Sale, self).set_shipment_cost()


class SaleLine:
    __name__ = 'sale.line'

    @classmethod
    def get_shipment_line(cls, product, price, sale=None, party=None):
        '''Get shipment line
        :param product: obj
        :param price: Decimal
        return obj
        '''
        pool = Pool()
        Tax = pool.get('account.tax')
        SaleLine = pool.get('sale.line')

        taxes = product.customer_taxes_used
        if taxes and party and party.customer_tax_rule:
            new_taxes = []
            for tax in taxes:
                tax_ids = party.customer_tax_rule.apply(tax, pattern={})
                new_taxes = new_taxes + tax_ids
            if new_taxes:
                taxes = Tax.browse(new_taxes)

        shipment_line = SaleLine()
        shipment_line.sale = sale
        shipment_line.product = product
        shipment_line.description = product.rec_name
        shipment_line.quantity = 1
        shipment_line.unit = product.sale_uom
        shipment_line.unit_price = price
        shipment_line.shipment_cost = price
        shipment_line.amount = price
        shipment_line.taxes = taxes
        shipment_line.sequence = 9999
        shipment_line.on_change_product()
        shipment_line.unit_price = price
        shipment_line.shipment_cost = price
        # compatibility with sale_discount
        if hasattr(SaleLine, 'gross_unit_price'):
            shipment_line.gross_unit_price = price
            shipment_line.update_prices()
        return shipment_line

    @classmethod
    def esale_dict2lines(cls, sale, values):
        '''
        Return list sale lines
        :param sale: obj
        :param values: dict
        return list
        '''
        pool = Pool()
        Product = pool.get('product.product')
        ProductCode = pool.get('product.code')
        Line = pool.get('sale.line')

        def default_create_product(shop, code):
            return None

        lines = []
        for l in values:
            code = l.get('product')
            products = Product.search(['OR',
                    ('name', '=', code),
                    ('code', '=', code),
                    ], limit=1)
            if products:
                product, = products
            else:
                product_codes = ProductCode.search([
                        ('number', '=', code)
                        ], limit=1)
                if product_codes:
                    product = product_codes[0].product
                    products = [product]

            if not products:
                product_esale = getattr(Product,
                    'create_product_%s' % sale.shop.esale_shop_app,
                    default_create_product)
                product = product_esale(sale.shop, code)

            if product:
                quantity = l['quantity']
                line = Line.get_sale_line_data(sale, product, quantity)
                if l.get('unit_price') or l.get('unit_price') == Decimal('0.0'):
                    line.unit_price = l['unit_price']
                    if hasattr(line, 'gross_unit_price'):
                        line.gross_unit_price = l['unit_price']
                if l.get('description'):
                    line.description = l['description']
                if l.get('note'):
                    line.note = l['note']
                if l.get('sequence'):
                    line.sequence = l['sequence']
                lines.append(line)
        return lines
