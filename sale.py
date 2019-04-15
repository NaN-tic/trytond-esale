# This file is part esale module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from decimal import Decimal
from trytond import backend
from trytond.model import fields, Unique
from trytond.pyson import Eval
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.config import config as config_
import logging

__all__ = ['Sale', 'SaleLine', 'Cron']

DIGITS = config_.getint('product', 'price_decimal', default=4)
PRECISION = Decimal(str(10.0 ** - DIGITS))
logger = logging.getLogger(__name__)
_ESALE_SALE_EXCLUDE_FIELDS = ['shipping_price', 'shipping_note', 'discount',
    'discount_description', 'coupon_code', 'coupon_description', 'carrier',
    'currency', 'payment']


class Cron(metaclass=PoolMeta):
    __name__ = 'ir.cron'

    @classmethod
    def __setup__(cls):
        super(Cron, cls).__setup__()
        cls.method.selection.extend([
            ('sale.shop|import_cron_orders', "eSale - Import Sales"),
            ('sale.shop|export_cron_state', "eSale - Export State"),
        ])


class Sale(metaclass=PoolMeta):
    __name__ = 'sale.sale'
    esale = fields.Boolean('eSale',
        states={
            'readonly': Eval('state') != 'draft',
            },
        depends=['state'])
    number_external = fields.Char('External Number', readonly=True,
        select=True)
    esale_coupon = fields.Char('eSale Coupon', readonly=True)
    status = fields.Char('eSale Status', readonly=True,
        help='Last status import/export to e-commerce APP')
    status_history = fields.Text('eSale Status history', readonly=True)
    carrier_tracking_ref = fields.Function(fields.Char('Carrier Tracking Ref'),
        'get_carrier_tracking_ref')
    number_packages = fields.Function(fields.Integer('Number of Packages'),
        'get_number_packages')

    @classmethod
    def __setup__(cls):
        super(Sale, cls).__setup__()
        t = cls.__table__()
        cls._sql_constraints.extend([
            ('number_external_uniq', Unique(t, t.shop, t.number_external),
             'There is another sale with the same number external.\n'
             'The number external of the sale must be unique!')
        ])

    @classmethod
    def __register__(cls, module_name):
        TableHandler = backend.get('TableHandler')

        table = TableHandler(cls, module_name)

        # Migration from 3.8: rename reference_external into number_external
        if (table.column_exist('reference_external')
                and not table.column_exist('number_external')):
            table.column_rename('reference_external', 'number_external')

        super(Sale, cls).__register__(module_name)

    @classmethod
    def copy(cls, sales, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default['number_external'] = None
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
    def create_external_order(cls, shop, sale_values={}, lines_values=[],
            extralines_values=[], party_values={}, invoice_values={},
            shipment_values={}):
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
        for k, v in sale_values.items():
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
            sale.number = sale_values.get('number_external')

        # esale coupon code
        if sale_values.get('coupon_code'):
            sale.esale_coupon = sale_values['coupon_code']

        # Currency
        currencies = Currency.search([
                ('code', '=', sale_values.get('currency')),
                ], limit=1)
        if currencies:
            currency, = currencies
            sale.currency = currency
        else:
            currency = shop.currency
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
        shipment_price = Decimal(sale_values.get('shipping_price', 0))
        shipment_values = [{
                'product': product_delivery.code or product_delivery.name,
                'quantity': 1,
                'unit_price': shipment_price.quantize(PRECISION),
                'description': shipment_description,
                'note': sale_values.get('shipping_note'),
                'sequence': 9999,
                }]
        shipment_line, = Line.esale_dict2lines(sale, shipment_values)
        shipment_line.shipment_cost = shipment_price.quantize(
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
                apply_discount_to_lines=False,
                ):
            sale.save()
            logger.info('Shop %s. Saved sale %s' % (
                shop.name, sale.number_external))

            if status:
                number = sale.number_external
                if sale_status.quote:
                    Sale.quote([sale])
                    if sale_status.confirm:
                        Sale.confirm([sale])
                        if sale_status.process:
                            Sale.process([sale])
                if sale_status.cancel:
                    Sale.cancel([sale])
                logger.info('Sale %s: %s' % (number, sale.state))
        Transaction().commit()

    def set_shipment_cost(self):
        # not set shipment cost when sale is generated from eSale
        if self.esale:
            return []
        return super(Sale, self).set_shipment_cost()

    def get_shipment_cost_line(self, cost):
        Line = Pool().get('sale.line')

        cost_line = super(Sale, self).get_shipment_cost_line(cost)

        sale_fields = Line._fields.keys()
        # add default values in cost line
        default_values = Line.default_get(sale_fields, with_rec_name=False)
        for k in default_values:
            if not hasattr(cost_line, k):
                setattr(cost_line, k, default_values[k])
        # add all sale line fields in cost line
        for k in sale_fields:
            if not hasattr(cost_line, k):
                setattr(cost_line, k, None)
        return cost_line

    def get_carrier_tracking_ref(self, name):
        refs = []
        for shipment in self.shipments:
            if not hasattr(shipment, 'carrier_tracking_ref'):
                return
            if shipment.carrier_tracking_ref:
                refs.append(shipment.carrier_tracking_ref)
        if refs:
            return ','.join(refs)

    def get_number_packages(self, name):
        packages = 0
        for shipment in self.shipments:
            if not hasattr(shipment, 'number_packages'):
                return
            if shipment.number_packages:
                packages += shipment.number_packages
        return packages

    @classmethod
    def _check_stock_quantity(cls, sales):
        # Not check stock quantity (user warning) according the context
        if not Transaction().context.get('without_warning', False):
            super(Sale, cls)._check_stock_quantity(sales)

    def esale_sale_export_csv(self):
        vals = {}
        if self.shop.esale_ext_reference:
            number = self.reference_external or self.number
        else:
            number = self.number
        vals['number'] = number
        vals['state'] = self.state
        return vals


class SaleLine(metaclass=PoolMeta):
    __name__ = 'sale.line'

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
                if l.get('discount_percent'):
                    line.discount = l['discount_percent']
                if l.get('gross_unit_price'):
                    line.gross_unit_price = l['gross_unit_price']
                if l.get('description'):
                    line.description = l['description']
                if l.get('note'):
                    line.note = l['note']
                if l.get('sequence'):
                    line.sequence = l['sequence']
                if l.get('discount_amount'):
                    line.discount_amount = l['discount_amount']
                if hasattr(line, 'gross_unit_price_wo_round'):
                    line.update_prices()
                line.amount = line.on_change_with_amount()
                lines.append(line)
        return lines
