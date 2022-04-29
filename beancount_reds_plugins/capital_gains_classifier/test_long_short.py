__copyright__ = "Copyright (C) 2021  Red S"
__license__ = "GNU GPLv3"

import unittest
import re

from beancount_reds_plugins.capital_gains_classifier.long_short import long_short
from beancount.core import data
from beancount.parser import options
from beancount import loader
from decimal import Decimal

# TODO:
# def test_auto_lot_matching(self, entries, _, options_map):
# def test_mixed_with_losses(self, entries, _, options_map):
# def test_long_leap_year(self, entries, _, options_map):

config = """{
   'Income.*:Capital-Gains': [':Capital-Gains', ':Capital-Gains:Short', ':Capital-Gains:Long']
   }"""


def get_entries_with_narration(entries, regexp):
    """Return the entries whose narration matches the regexp.

    Args:
      entries: A list of directives.
      regexp: A regular expression string, to be matched against the
        narration field of transactions.
    Returns:
      A list of directives.
    """
    return [entry
            for entry in entries
            if (isinstance(entry, data.Transaction) and
                re.search(regexp, entry.narration))]


class TestLongShort(unittest.TestCase):

    def test_empty_entries(self):
        entries, _ = long_short([], options.OPTIONS_DEFAULTS.copy(), config)
        self.assertEqual([], entries)

    @loader.load_doc()
    def test_do_not_touch(self, entries, _, options_map):
        """
        plugin "beancount.plugins.auto"

        2014-02-01 * "Buy"
          Assets:Brokerage    100 ORNG {1 USD}
          Assets:Bank        -100 USD

        2014-03-01 * "Sell"
          Assets:Brokerage   -100 ORNG {1 USD} @ 1.50 USD
          Assets:Bank         140 USD
          Income:Capital-Gains:Short -20 USD
          Income:Capital-Gains       -30 USD
          Expenses:Fees        10 USD

        """
        new_entries, _ = long_short(entries, options_map, config)
        self.assertEqual(new_entries, entries)

    @loader.load_doc()
    def test_long(self, entries, _, options_map):
        """
        2014-01-01 open Assets:Brokerage
        2014-01-01 open Assets:Bank
        2014-01-01 open Income:Capital-Gains

        2014-02-01 * "Buy"
          Assets:Brokerage    100 ORNG {1 USD}
          Assets:Bank        -100 USD

        2016-03-01 * "Sell"
          Assets:Brokerage   -100 ORNG {1 USD} @ 1.50 USD
          Assets:Bank         150 USD
          Income:Capital-Gains

        """

        # # # Above should turn into:
        # 2014-03-01 * "Sell"
        #   Assets:Brokerage   -100 ORNG {1 USD} @ 1.50 USD
        #   Assets:Bank         150 USD
        #   Income:Capital-Gains:Long -50 USD

        new_entries, _ = long_short(entries, options_map, config)
        self.assertEqual(6, len(new_entries))

        results = get_entries_with_narration(new_entries, "Sell")
        self.assertEqual('Income:Capital-Gains:Long', results[0].postings[2].account)
        self.assertEqual(Decimal("-50.00"), results[0].postings[2].units.number)

    @loader.load_doc()
    def test_long_exactly_one_year_and_month(self, entries, _, options_map):
        """
        2014-01-01 open Assets:Brokerage
        2014-01-01 open Assets:Bank
        2014-01-01 open Income:Capital-Gains

        2014-02-01 * "Buy"
          Assets:Brokerage    100 ORNG {1 USD}
          Assets:Bank        -100 USD

        2015-03-01 * "Sell"
          Assets:Brokerage   -100 ORNG {1 USD} @ 1.50 USD
          Assets:Bank         150 USD
          Income:Capital-Gains

        """

        # # # Above should turn into:
        # 2014-03-01 * "Sell"
        #   Assets:Brokerage   -100 ORNG {1 USD} @ 1.50 USD
        #   Assets:Bank         150 USD
        #   Income:Capital-Gains:Long -50 USD

        new_entries, _ = long_short(entries, options_map, config)
        self.assertEqual(6, len(new_entries))

        results = get_entries_with_narration(new_entries, "Sell")
        self.assertEqual('Income:Capital-Gains:Long', results[0].postings[2].account)
        self.assertEqual(Decimal("-50.00"), results[0].postings[2].units.number)

    @loader.load_doc()
    def test_short(self, entries, _, options_map):
        """
        2014-01-01 open Assets:Brokerage
        2014-01-01 open Assets:Bank
        2014-01-01 open Income:Capital-Gains

        2014-02-01 * "Buy"
          Assets:Brokerage    100 ORNG {1 USD}
          Assets:Bank        -100 USD

        2014-03-01 * "Sell"
          Assets:Brokerage   -100 ORNG {1 USD} @ 1.50 USD
          Assets:Bank         150 USD
          Income:Capital-Gains

        """
        new_entries, _ = long_short(entries, options_map, config)
        self.assertEqual(6, len(new_entries))
        results = get_entries_with_narration(new_entries, "Sell")
        self.assertEqual('Income:Capital-Gains:Short', results[0].postings[2].account)
        self.assertEqual(Decimal("-50.00"), results[0].postings[2].units.number)

    @loader.load_doc()
    def test_mixed(self, entries, _, options_map):
        """
        2014-01-01 open Assets:Brokerage
        2014-01-01 open Assets:Bank
        2014-01-01 open Income:Capital-Gains

        2014-02-01 * "Buy"
          Assets:Brokerage    100 ORNG {1 USD}
          Assets:Bank        -100 USD

        2016-02-01 * "Buy"
          Assets:Brokerage    100 ORNG {2 USD}
          Assets:Bank        -200 USD

        2016-03-01 * "Sell"
          Assets:Brokerage   -100 ORNG {1 USD} @ 2.50 USD
          Assets:Brokerage   -100 ORNG {2 USD} @ 2.50 USD
          Assets:Bank         500 USD
          Income:Capital-Gains

        """
        new_entries, _ = long_short(entries, options_map, config)
        self.assertEqual(8, len(new_entries))
        results = get_entries_with_narration(new_entries, "Sell")
        self.assertEqual('Income:Capital-Gains:Short', results[0].postings[3].account)
        self.assertEqual(Decimal("-50.00"), results[0].postings[3].units.number)
        self.assertEqual('Income:Capital-Gains:Long', results[0].postings[4].account)
        self.assertEqual(Decimal("-150.00"), results[0].postings[4].units.number)

    @loader.load_doc()
    def test_leap_year(self, entries, _, options_map):
        """
        2014-01-01 open Assets:Brokerage
        2014-01-01 open Assets:Bank
        2014-01-01 open Income:Capital-Gains

        2016-02-28 * "Buy"
          Assets:Brokerage    100 ORNG {1 USD}
          Assets:Bank        -100 USD

        2017-02-28 * "Sell"
          Assets:Brokerage   -100 ORNG {1 USD} @ 1.50 USD
          Assets:Bank         150 USD
          Income:Capital-Gains

        """

        # # # Above should turn into:
        # 2014-03-01 * "Sell"
        #   Assets:Brokerage   -100 ORNG {1 USD} @ 1.50 USD
        #   Assets:Bank         150 USD
        #   Income:Capital-Gains:Long -50 USD

        new_entries, _ = long_short(entries, options_map, config)
        self.assertEqual(6, len(new_entries))

        results = get_entries_with_narration(new_entries, "Sell")
        self.assertEqual('Income:Capital-Gains:Short', results[0].postings[2].account)
        self.assertEqual(Decimal("-50.00"), results[0].postings[2].units.number)

    @loader.load_doc()
    def test_fee(self, entries, _, options_map):
        """
        2014-01-01 open Assets:Brokerage
        2014-01-01 open Assets:Bank
        2014-01-01 open Expenses:Fees
        2014-01-01 open Income:Capital-Gains

        2014-02-01 * "Buy"
          Assets:Brokerage    100 ORNG {1 USD}
          Assets:Bank        -100 USD

        2014-03-01 * "Sell"
          Assets:Brokerage   -100 ORNG {1 USD} @ 1.50 USD
          Assets:Bank         140 USD
          Income:Capital-Gains
          Expenses:Fees        10 USD

        """
        new_entries, _ = long_short(entries, options_map, config)
        self.assertEqual(7, len(new_entries))
        results = get_entries_with_narration(new_entries, "Sell")
        self.assertEqual('Income:Capital-Gains:Short', results[0].postings[3].account)
        self.assertEqual(Decimal("-50.00"), results[0].postings[3].units.number)

    @loader.load_doc()
    def test_shortposition_reduction(self, entries, _, options_map):
        """
        2014-01-01 open Assets:Brokerage
        2014-01-01 open Assets:Bank
        2014-01-01 open Expenses:Fees
        2014-01-01 open Income:Capital-Gains

        2014-02-01 * "Buy Short position"
          Assets:Brokerage   -100 ORNG {1 USD}
          Assets:Bank         100 USD

        2015-03-01 * "Sell Short position"
          Assets:Brokerage    100 ORNG {1 USD} @ 0.50 USD
          Assets:Bank         -50 USD
          Income:Capital-Gains

        """
        new_entries, _ = long_short(entries, options_map, config)
        self.assertEqual(7, len(new_entries))
        results = get_entries_with_narration(new_entries, "Sell Short position")
        self.assertEqual('Income:Capital-Gains:Long', results[0].postings[2].account)
        self.assertEqual(Decimal("-50.00"), results[0].postings[2].units.number)
