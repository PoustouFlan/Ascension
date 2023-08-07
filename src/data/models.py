from typing import Optional

from tortoise.models import Model
from tortoise import fields
from datetime import date

import logging
log = logging.getLogger("Ascension")

def strptime(date_str):
    day, month, year = date_str.split()
    month = [None, 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug',
              'Sep', 'Oct', 'Nov', 'Dec'].index(month)
    return date(int(year), month, int(day))
