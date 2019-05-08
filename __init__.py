# This file is part esale module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from . import configuration
from . import esale
from . import party
from . import address
from . import shop
from . import sale
from . import stock
from . import product
from . import carrier

def register():
    Pool.register(
        carrier.Carrier,
        configuration.Configuration,
        configuration.ConfigurationSaleEsale,
        party.Party,
        address.Address,
        shop.EsaleSaleExportCSVStart,
        shop.EsaleSaleExportCSVResult,
        shop.SaleShop,
        shop.SaleShopWarehouse,
        shop.SaleShopCountry,
        shop.SaleShopLang,
        sale.Cron,
        sale.Sale,
        sale.SaleLine,
        stock.ShipmentOut,
        esale.eSaleCarrier,
        esale.eSalePayment,
        esale.eSaleStatus,
        esale.eSaleSate,
        esale.eSaleAccountTaxRule,
        product.Template,
        product.Product,
        module='esale', type_='model')
    Pool.register(
        shop.EsaleSaleExportCSV,
        module='esale', type_='wizard')
