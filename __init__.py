# This file is part esale module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
import configuration
import esale
import party
import address
import shop
import sale
import stock
import product
import carrier

def register():
    Pool.register(
        carrier.Carrier,
        configuration.Configuration,
        party.Party,
        address.Address,
        shop.EsaleSaleExportCSVStart,
        shop.EsaleSaleExportCSVResult,
        shop.SaleShop,
        shop.SaleShopWarehouse,
        shop.SaleShopCountry,
        shop.SaleShopLang,
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
