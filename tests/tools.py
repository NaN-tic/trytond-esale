#This file is part esale module for Tryton.
#The COPYRIGHT file at the top level of this repository contains
#the full copyright notices and license terms.

__all__ = ['sale_values', 'lines_values', 'party_values', 'invoice_values',
    'shipment_values']

def sale_values(reference):
    vals = {
        'reference_external': reference,
        'carrier': 'carrier',
        'payment': 'cash',
        'currency': 'EUR',
        'comment': 'Example Sale Order',
        'status': 'paid',
        'status_history': 'status history',
        'external_untaxed_amount': '20.00',
        'external_tax_amount': '5.00',
        'external_total_amount': '25.00',
        'external_shipment_amount': '12.10',
        'shipping_price': '10.00',
        'shipping_note': 'eSale External',
        'discount': '',
        'discount_description': '',
        'coupon_code': '',
        'coupon_description': '',
        }
    return vals

def lines_values(code):
    vals = {
        'product': code,
        'quantity': '1.0',
        'description': 'Product eSale',
        'unit_price': '10.00',
        'note': '',
        'sequence': 1,
        }
    return vals

def party_values():
    vals = {
        'name': 'Customer',
        'esale_email': 'email@domain.com',
        'vat_code': 'A78109592',
        'vat_country': 'ES',
        }
    return vals

def invoice_values():
    vals = {
        'name': 'Invoice Address',
        'street': 'Durruti',
        'zip': '08000',
        'city': 'Barcelona',
        'subdivision': '',
        'country': 'ES',
        'phone': '0034890',
        'email': 'email@domain.com',
        'fax': '',
        }
    return vals

def shipment_values():
    vals = {
        'name': 'Delivery Address',
        'street': 'Ovidi Montllor',
        'zip': '08000',
        'city': 'Barcelona',
        'subdivision': '',
        'country': 'ES',
        'phone': '0034890',
        'email': 'email@domain.com',
        'fax': '',
        }
    return vals
