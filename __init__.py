#This file is part esale module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.
from trytond.pool import Pool
from .configuration import *
from .shop import *
from .sale import *

def register():
    Pool.register(
        Configuration,
        SaleShop,
        SaleShopCountry,
        SaleShopLang,
        Sale,
        module='esale', type_='model')
