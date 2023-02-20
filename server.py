# stock-price-analysis
Analyzing the trading opportunities for stock A and stock B by processing their data feeds.

################################################################################
#
#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software and associated documentation files (the "Software"),
#  to deal in the Software without restriction, including without limitation
#  the rights to use, copy, modify, merge, publish, distribute, sublicense,
#  and/or sell copies of the Software, and to permit persons to whom the
#  Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#  OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.

import csv
import http.server
import json
import operator
import os.path
import re
import threading
from datetime import timedelta, datetime
from random import normalvariate, random
from socketserver import ThreadingMixIn

import dateutil.parser

################################################################################
#
# Config

# Sim params

REALTIME = True
SIM_LENGTH = timedelta(days=365 * 5)
MARKET_OPEN = datetime.today().replace(hour=0, minute=30, second=0)

# Market parms
#       min  / max  / std
SPD = (2.0, 6.0, 0.1)
PX = (60.0, 150.0, 1)
FREQ = (12, 36, 50)

# Trades

OVERLAP = 4


################################################################################
#
# Test Data

def bwalk(min, max, std):
    """ Generates a bounded random walk. """
    rng = max - min
    while True:
        max += normalvariate(0, std)
        yield abs((max % (rng * 2)) - rng) + min


def market(t0=MARKET_OPEN):
    """ Generates a random series of market conditions,
        (time, price, spread).
    """
    for hours, px, spd in zip(bwalk(*FREQ), bwalk(*PX), bwalk(*SPD)):
        yield t0, px, spd
        t0 += timedelta(hours=abs(hours))


def orders(hist):
    """ Generates a random set of limit orders (time, side, price, size) from
        a series of market conditions.
    """
    for t, px, spd in hist:
        stock = 'ABC' if random() > 0.5 else 'DEF'
        side, d = ('sell', 2) if random() > 0.5 else ('buy', -2)
        order = round(normalvariate(px + (spd / d), spd / OVERLAP), 2)
        size = int(abs(normalvariate(0, 100)))
        yield t, stock, side, order, size


################################################################################
#
# Order Book

def add_book(book, order, size, _age=10):
    """ Add a new order and size to a book, and age the rest of the book. """
    yield order, size, _age
    for o, s, age in book:
        if age > 0:
           
