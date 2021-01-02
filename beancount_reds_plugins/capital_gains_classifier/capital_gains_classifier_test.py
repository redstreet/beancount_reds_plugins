__copyright__ = "Copyright (C) 2015-2016  Martin Blais"
__license__ = "GNU GPLv2"

import unittest

from beancount.core import data
from beancount.parser import cmptest
from beancount.parser import printer
from beancount import loader
from . import capital_gains_classifier


class TestLossGains(cmptest.TestCase):
    @loader.load_doc()
    def test_loss_gains(self, entries, errors, _):
        """
        plugin "capital_gains_classifier" "{
         'Income.*:Capital-Gains.*': {
            'match':  ':Capital-Gains',
            'gains':  ':Capital-Gains:Gains',
            'losses': ':Capital-Gains:Losses'},
         }"

        2015-01-01 open Assets:Brokerage "STRICT"
        2015-01-01 open Assets:Bank
        2015-01-01 open Income:Capital-Gains

        2019-01-01 * "Buy"
          Assets:Brokerage 100 HOOLI {1 USD}
          Assets:Bank -100 USD

        2019-12-01 * "Sell"
          Assets:Brokerage -50 HOOLI {1 USD} @ 2 USD
          Assets:Bank      100 USD
          Income:Capital-Gains

        2020-01-25 * "Sell"
          Assets:Brokerage -50 HOOLI {1 USD} @ 0.5 USD
          Assets:Bank       25 USD
          Income:Capital-Gains
        """
        self.assertEqualEntries("""

        2019-01-01 * "Buy"
          Assets:Brokerage 100 HOOLI {1 USD}
          Assets:Bank -100 USD

        2019-12-01 * "Sell"
          Assets:Brokerage -50 HOOLI {1 USD} @ 2 USD
          Assets:Bank      100 USD
          Income:Capital-Gains:Gains -50 USD


        2020-01-25 * "Sell"
          Assets:Brokerage -50 HOOLI {1 USD} @ 0.5 USD
          Assets:Bank       25 USD
          Income:Capital-Gains:Losses 25 USD

        """, list(data.filter_txns(entries)))

#class TestLongShort(cmptest.TestCase):
#    @loader.load_doc()
#    def test_long_short_simple(self, entries, errors, _):
#        """
#        plugin "capital_gains_classifier" "{
#         'Income.*:Capital-Gains.*': {
#            'match':  ':Capital-Gains',
#            'gains':  ':Capital-Gains:Gains',
#            'losses': ':Capital-Gains:Losses'},
#         }"
#
#        2015-01-01 open Assets:Brokerage "STRICT"
#        2015-01-01 open Assets:Bank
#        2015-01-01 open Income:Capital-Gains
#
#        2019-01-01 * "Buy"
#          Assets:Brokerage 100 HOOLI {1 USD}
#          Assets:Bank -100 USD
#
#        2019-12-01 * "Sell"
#          Assets:Brokerage -50 HOOLI {1 USD} @ 2 USD
#          Assets:Bank      100 USD
#          Income:Capital-Gains
#
#        2020-01-25 * "Sell"
#          Assets:Brokerage -50 HOOLI {1 USD} @ 0.5 USD
#          Assets:Bank       25 USD
#          Income:Capital-Gains
#        """
#        self.assertEqualEntries("""
#
#        2019-01-01 * "Buy"
#          Assets:Brokerage 100 HOOLI {1 USD}
#          Assets:Bank -100 USD
#
#        2019-12-01 * "Sell"
#          Assets:Brokerage -50 HOOLI {1 USD} @ 2 USD
#          Assets:Bank      100 USD
#          Income:Capital-Gains:Gains -50 USD
#
#
#        2020-01-25 * "Sell"
#          Assets:Brokerage -50 HOOLI {1 USD} @ 0.5 USD
#          Assets:Bank       25 USD
#          Income:Capital-Gains:Losses 25 USD
#
#        """, list(data.filter_txns(entries)))

if __name__ == '__main__':
    unittest.main()
