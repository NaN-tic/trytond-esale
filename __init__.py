#This file is part esale module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.
from trytond.pool import Pool
from .configuration import *
from .party import *
from .address import *
from .shop import *
from .sale import *

def register():
    Pool.register(
        Configuration,
        Party,
        Address,
        SaleShop,
        SaleShopCountry,
        SaleShopLang,
        Sale,
        SaleLine,
        module='esale', type_='model')
