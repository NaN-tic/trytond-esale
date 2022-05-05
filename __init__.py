# This file is part esale module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from . import esale
from . import party
from . import shop
from . import sale
from . import stock
from . import product
from . import carrier

def register():
    Pool.register(
        carrier.Carrier,
        party.Party,
        party.Address,
        shop.SaleShop,
        shop.SaleShopWarehouse,
        shop.SaleShopCountry,
        shop.SaleShopLang,
        sale.Sale,
        stock.ShipmentOut,
        esale.eSaleCarrier,
        esale.eSalePayment,
        product.Template,
        product.Product,
        module='esale', type_='model')
