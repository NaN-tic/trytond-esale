#This file is part esale module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.

import logging
import time

try:
    import slug
except ImportError:
    logging.getLogger('esale').error(
            'Unable to import slug. Install slug package.')

def slugify(value):
    """Convert value to slug: az09 and replace spaces by -"""
    try:
        if isinstance(value, unicode):
            name = slug.slug(value)
        else:
            name = slug.slug(unicode(value, 'UTF-8'))
    except:
        name = ''
    return name

def convert_gmtime(date):
    """Convert UTC timezone"""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.mktime(time.strptime(date, "%Y-%m-%d %H:%M:%S"))))
