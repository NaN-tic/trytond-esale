#This file is part esale module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.
{
    'name': 'eSale',
    'name_ca_ES': 'eSale',
    'name_es_ES': 'eSale',
    'version': '2.4.0',
    'author': 'Zikzakmedia',
    'email': 'zikzak@zikzakmedia.com',
    'website': 'http://www.zikzakmedia.com/',
    'description': '''eSale tools''',
    'description_ca_ES': '''Comerç electrònic''',
    'description_es_ES': '''Comercio electrónico''',
    'depends': [
        'carrier',
        'sale_shop',
    ],
    'xml': [
        'shop.xml',
    ],
    'translation': [
        'locale/ca_ES.po',
        'locale/es_ES.po',
    ]
}
