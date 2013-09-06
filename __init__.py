#This file is part esale module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.
from trytond.pool import Pool
from .shop import *
from .configuration import *

def register():
    Pool.register(
        Configuration,
        SaleShop,
        SaleShopCountry,
        SaleShopLang,
        module='esale', type_='model')
