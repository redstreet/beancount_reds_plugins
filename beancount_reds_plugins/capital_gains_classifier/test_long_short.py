__copyright__ = "Copyright (C) 2021  Red S"
__license__ = "GNU GPLv3"

from beancount_reds_plugins.capital_gains_classifier.long_short import long_short
from beancount.parser import options
from beancount import loader
from beancount.parser import cmptest

# TODO:
# def test_auto_lot_matching(self, entries, _, options_map):
# def test_mixed_with_losses(self, entries, _, options_map):
# def test_long_leap_year(self, entries, _, options_map):

config = """{
   'Income.*:Capital-Gains': [':Capital-Gains', ':Capital-Gains:Short', ':Capital-Gains:Long']
   }"""


class TestLongShort(cmptest.TestCase):
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

        new_entries, _ = long_short(entries, options_map, config)

        self.assertEqualEntries("""
        2014-01-01 open Assets:Brokerage
        2014-01-01 open Assets:Bank
        2014-01-01 open Income:Capital-Gains
        2014-01-01 open Income:Capital-Gains:Long

        2014-02-01 * "Buy"
          Assets:Brokerage    100 ORNG {1 USD}
          Assets:Bank        -100 USD

        2016-03-01 * "Sell"
          Assets:Brokerage   -100 ORNG {1 USD} @ 1.50 USD
          Assets:Bank         150 USD
          Income:Capital-Gains:Long -50.00 USD
        """, new_entries)

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

        new_entries, _ = long_short(entries, options_map, config)

        self.assertEqualEntries("""
        2014-01-01 open Assets:Brokerage
        2014-01-01 open Assets:Bank
        2014-01-01 open Income:Capital-Gains
        2014-01-01 open Income:Capital-Gains:Long

        2014-02-01 * "Buy"
          Assets:Brokerage    100 ORNG {1 USD}
          Assets:Bank        -100 USD

        2015-03-01 * "Sell"
          Assets:Brokerage   -100 ORNG {1 USD} @ 1.50 USD
          Assets:Bank         150 USD
          Income:Capital-Gains:Long -50.00 USD
        """, new_entries)

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

        self.assertEqualEntries("""
        2014-01-01 open Assets:Brokerage
        2014-01-01 open Assets:Bank
        2014-01-01 open Income:Capital-Gains
        2014-01-01 open Income:Capital-Gains:Short

        2014-02-01 * "Buy"
          Assets:Brokerage    100 ORNG {1 USD}
          Assets:Bank        -100 USD

        2014-03-01 * "Sell"
          Assets:Brokerage   -100 ORNG {1 USD} @ 1.50 USD
          Assets:Bank         150 USD
          Income:Capital-Gains:Short -50.00 USD
        """, new_entries)

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

        self.assertEqualEntries("""
        2014-01-01 open Assets:Brokerage
        2014-01-01 open Assets:Bank
        2014-01-01 open Income:Capital-Gains
        2014-01-01 open Income:Capital-Gains:Long
        2014-01-01 open Income:Capital-Gains:Short

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
          Income:Capital-Gains:Short  -50.0000 USD
          Income:Capital-Gains:Long  -150.0000 USD
        """, new_entries)

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

        new_entries, _ = long_short(entries, options_map, config)

        self.assertEqualEntries("""
        2014-01-01 open Assets:Brokerage
        2014-01-01 open Assets:Bank
        2014-01-01 open Income:Capital-Gains
        2014-01-01 open Income:Capital-Gains:Short

        2016-02-28 * "Buy"
          Assets:Brokerage    100 ORNG {1 USD}
          Assets:Bank        -100 USD

        2017-02-28 * "Sell"
          Assets:Brokerage   -100 ORNG {1 USD} @ 1.50 USD
          Assets:Bank         150 USD
          Income:Capital-Gains:Short -50.00 USD
        """, new_entries)

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

        self.assertEqualEntries("""
        2014-01-01 open Assets:Brokerage
        2014-01-01 open Assets:Bank
        2014-01-01 open Expenses:Fees
        2014-01-01 open Income:Capital-Gains
        2014-01-01 open Income:Capital-Gains:Short

        2014-02-01 * "Buy"
          Assets:Brokerage    100 ORNG {1 USD}
          Assets:Bank        -100 USD

        2014-03-01 * "Sell"
          Assets:Brokerage   -100 ORNG {1 USD} @ 1.50 USD
          Assets:Bank         140 USD
          Income:Capital-Gains:Short -50.00 USD
          Expenses:Fees        10 USD
        """, new_entries)

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

        self.assertEqualEntries("""
        2014-01-01 open Assets:Brokerage
        2014-01-01 open Assets:Bank
        2014-01-01 open Expenses:Fees
        2014-01-01 open Income:Capital-Gains
        2014-01-01 open Income:Capital-Gains:Long

        2014-02-01 * "Buy Short position"
          Assets:Brokerage   -100 ORNG {1 USD}
          Assets:Bank         100 USD

        2015-03-01 * "Sell Short position"
          Assets:Brokerage    100 ORNG {1 USD} @ 0.50 USD
          Assets:Bank         -50 USD
          Income:Capital-Gains:Long -50.00 USD
        """, new_entries)

    @loader.load_doc()
    def test_zero_missing_price(self, entries, _, options_map):
        """
        2014-01-01 open Assets:Brokerage
        2014-01-01 open Assets:Bank
        2014-01-01 open Income:Capital-Gains

        2014-02-01 * "Buy"
          Assets:Brokerage    100 ORNG {1 USD}
          Assets:Bank        -100 USD

        2016-03-01 * "Sell at complete loss"
          Assets:Brokerage   -50 ORNG {1 USD} @ 0 USD
          Income:Capital-Gains

        2016-03-01 * "Sell but forgot price"
          Assets:Brokerage   -50 ORNG {1 USD}
          Assets:Bank 100 USD
          Income:Capital-Gains
        """
        new_entries, _ = long_short(entries, options_map, config)

        self.assertEqualEntries("""
        2014-01-01 open Assets:Brokerage
        2014-01-01 open Assets:Bank
        2014-01-01 open Income:Capital-Gains
        2014-01-01 open Income:Capital-Gains:Long

        2014-02-01 * "Buy"
          Assets:Brokerage    100 ORNG {1 USD}
          Assets:Bank        -100 USD

        2016-03-01 * "Sell at complete loss"
          Assets:Brokerage           -50 ORNG {1 USD, 2014-02-01} @ 0 USD
          Income:Capital-Gains:Long   50 USD

        2016-03-01 * "Sell but forgot price"
          Assets:Brokerage      -50 ORNG {1 USD, 2014-02-01}
          Assets:Bank           100 USD
          Income:Capital-Gains  -50 USD

        """, new_entries)
