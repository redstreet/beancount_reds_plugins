__copyright__ = "Copyright (C) 2021  Red S"
__license__ = "GNU GPLv3"

from decimal import Decimal

from beancount import loader
from beancount.core import data
from beancount.parser import cmptest, options

from beancount_reds_plugins.capital_gains_classifier.long_short import long_short

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

        self.assertEqualEntries(
            """
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
        """,
            new_entries,
        )

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

        self.assertEqualEntries(
            """
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
        """,
            new_entries,
        )

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

        self.assertEqualEntries(
            """
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
        """,
            new_entries,
        )

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

        self.assertEqualEntries(
            """
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
          Income:Capital-Gains:Short  -50.00 USD
          Income:Capital-Gains:Long  -150.00 USD
        """,
            new_entries,
        )

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

        self.assertEqualEntries(
            """
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
        """,
            new_entries,
        )

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

        self.assertEqualEntries(
            """
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
        """,
            new_entries,
        )

    @loader.load_doc()
    def test_shortposition_reduction(self, entries, _, options_map):
        """
        2014-01-01 open Assets:Brokerage
        2014-01-01 open Assets:Bank
        2014-01-01 open Expenses:Fees
        2014-01-01 open Income:Capital-Gains

        2014-02-01 * "Buy Short position"
          Assets:Brokerage   -100 ORNG {1 USD}
          Assets:Bank        100 USD

        2015-03-01 * "Sell Short position"
          Assets:Brokerage    100 ORNG {1 USD} @ 0.50 USD
          Assets:Bank         -50 USD
          Income:Capital-Gains
        """
        new_entries, _ = long_short(entries, options_map, config)

        # The cover of a short is short-term whatever its holding period
        # (US IRC 1234(b); 1233(a) for short sales), here held over a year.
        self.assertEqualEntries(
            """
        2014-01-01 open Assets:Brokerage
        2014-01-01 open Assets:Bank
        2014-01-01 open Expenses:Fees
        2014-01-01 open Income:Capital-Gains
        2014-01-01 open Income:Capital-Gains:Short

        2014-02-01 * "Buy Short position"
          Assets:Brokerage   -100 ORNG {1 USD}
          Assets:Bank        100 USD

        2015-03-01 * "Sell Short position"
          Assets:Brokerage    100 ORNG {1 USD} @ 0.50 USD
          Assets:Bank         -50 USD
          Income:Capital-Gains:Short -50.00 USD
        """,
            new_entries,
        )

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

        self.assertEqualEntries(
            """
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

        """,
            new_entries,
        )

    @staticmethod
    def without_cost_dates(entries):
        """Return the entries with every booked cost's date cleared.

        Booking always stamps a date, so this is how the tests express a
        reduction whose cost carries none.
        """
        return [
            e._replace(
                postings=[
                    p._replace(cost=p.cost._replace(date=None)) if p.cost else p
                    for p in e.postings
                ]
            )
            if isinstance(e, data.Transaction)
            else e
            for e in entries
        ]

    @loader.load_doc()
    def test_written_option_cover_is_short_term(self, entries, _, options_map):
        """
        2025-01-01 open Assets:Cash USD
        2025-01-01 open Assets:Options
        2025-01-01 open Income:Capital-Gains

        2025-03-03 * "Sell to open 1 AAPL Jan 2027 300 call @ 12.00"
          Assets:Options  -1 AAPL270115C00300000 {1200.00 USD}
          Assets:Cash     1200.00 USD

        2026-06-01 * "Buy to close @ 4.00"
          Assets:Options   1 AAPL270115C00300000 {} @ 400.00 USD
          Assets:Cash   -400.00 USD
          Income:Capital-Gains
        """
        new_entries, _ = long_short(entries, options_map, config)

        self.assertEqualEntries(
            """
        2025-01-01 open Assets:Cash USD
        2025-01-01 open Assets:Options
        2025-01-01 open Income:Capital-Gains
        2025-01-01 open Income:Capital-Gains:Short

        2025-03-03 * "Sell to open 1 AAPL Jan 2027 300 call @ 12.00"
          Assets:Options  -1 AAPL270115C00300000 {1200.00 USD, 2025-03-03}
          Assets:Cash     1200.00 USD

        2026-06-01 * "Buy to close @ 4.00"
          Assets:Options   1 AAPL270115C00300000 {1200.00 USD, 2025-03-03} @ 400.00 USD
          Assets:Cash   -400.00 USD
          Income:Capital-Gains:Short -800.00 USD
        """,
            new_entries,
        )

    @loader.load_doc()
    def test_cover_at_a_loss_is_short_term(self, entries, _, options_map):
        """
        2025-01-01 open Assets:Cash USD
        2025-01-01 open Assets:Options
        2025-01-01 open Income:Capital-Gains

        2025-03-03 * "Sell to open @ 4.00"
          Assets:Options  -1 AAPL270115C00300000 {400.00 USD}
          Assets:Cash     400.00 USD

        2026-06-01 * "Buy to close @ 12.00"
          Assets:Options   1 AAPL270115C00300000 {} @ 1200.00 USD
          Assets:Cash   -1200.00 USD
          Income:Capital-Gains
        """
        new_entries, _ = long_short(entries, options_map, config)

        # Bought back above what the written option sold for: a loss,
        # debited to income, and short-term like any cover.
        self.assertEqualEntries(
            """
        2025-01-01 open Assets:Cash USD
        2025-01-01 open Assets:Options
        2025-01-01 open Income:Capital-Gains
        2025-01-01 open Income:Capital-Gains:Short

        2025-03-03 * "Sell to open @ 4.00"
          Assets:Options  -1 AAPL270115C00300000 {400.00 USD, 2025-03-03}
          Assets:Cash     400.00 USD

        2026-06-01 * "Buy to close @ 12.00"
          Assets:Options   1 AAPL270115C00300000 {400.00 USD, 2025-03-03} @ 1200.00 USD
          Assets:Cash   -1200.00 USD
          Income:Capital-Gains:Short 800.00 USD
        """,
            new_entries,
        )

    @loader.load_doc()
    def test_cover_and_sale_split_by_the_rule(self, entries, _, options_map):
        """
        2024-01-01 open Assets:Brokerage
        2024-01-01 open Assets:Options
        2024-01-01 open Assets:Bank USD
        2024-01-01 open Income:Capital-Gains

        2024-01-15 * "Buy stock"
          Assets:Brokerage    10 AAPL {100 USD}
          Assets:Bank      -1000 USD

        2025-03-03 * "Sell to open a call"
          Assets:Options  -1 OPT {1200 USD}
          Assets:Bank      1200 USD

        2026-06-01 * "Sell the stock and cover the call"
          Assets:Brokerage  -10 AAPL {100 USD} @ 150 USD
          Assets:Options      1 OPT {} @ 400 USD
          Assets:Bank         1100 USD
          Income:Capital-Gains
        """
        new_entries, _ = long_short(entries, options_map, config)

        # One entry, one sale of a long lot and one cover: the term split
        # follows the units sign, and each leg's gain keeps its own sign
        # (a cover that won credits income).
        self.assertEqualEntries(
            """
        2024-01-01 open Assets:Brokerage
        2024-01-01 open Assets:Options
        2024-01-01 open Assets:Bank USD
        2024-01-01 open Income:Capital-Gains
        2024-01-01 open Income:Capital-Gains:Short
        2024-01-01 open Income:Capital-Gains:Long

        2024-01-15 * "Buy stock"
          Assets:Brokerage    10 AAPL {100 USD, 2024-01-15}
          Assets:Bank      -1000 USD

        2025-03-03 * "Sell to open a call"
          Assets:Options  -1 OPT {1200 USD, 2025-03-03}
          Assets:Bank      1200 USD

        2026-06-01 * "Sell the stock and cover the call"
          Assets:Brokerage  -10 AAPL {100 USD, 2024-01-15} @ 150 USD
          Assets:Options      1 OPT {1200 USD, 2025-03-03} @ 400 USD
          Assets:Bank         1100 USD
          Income:Capital-Gains:Short -800 USD
          Income:Capital-Gains:Long -500 USD
        """,
            new_entries,
        )

    @loader.load_doc()
    def test_cover_without_a_cost_date_is_short_term(self, entries, _, options_map):
        """
        2025-01-01 open Assets:Cash USD
        2025-01-01 open Assets:Options
        2025-01-01 open Income:Capital-Gains

        2025-03-03 * "Sell to open 1 AAPL Jan 2027 300 call @ 12.00"
          Assets:Options  -1 AAPL270115C00300000 {1200.00 USD}
          Assets:Cash     1200.00 USD

        2026-06-01 * "Buy to close @ 4.00"
          Assets:Options   1 AAPL270115C00300000 {} @ 400.00 USD
          Assets:Cash   -400.00 USD
          Income:Capital-Gains
        """
        new_entries, _ = long_short(
            self.without_cost_dates(entries), options_map, config
        )

        # A cover has no cost date to classify by and needs none.
        txn = [e for e in new_entries if isinstance(e, data.Transaction)][-1]
        short = [p for p in txn.postings if ":Short" in p.account]
        self.assertEqual(len(short), 1)
        self.assertEqual(short[0].units.number, Decimal("-800.00"))
        self.assertEqual(short[0].units.currency, "USD")

    @loader.load_doc()
    def test_no_cost_date_passes_through_unchanged(self, entries, _, options_map):
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
        new_entries, _ = long_short(
            self.without_cost_dates(entries), options_map, config
        )

        # A sale of a long lot with no cost date has no holding period to
        # classify by. Leave the entry alone rather than guess: the generic
        # gains posting stays and the transaction keeps its balance.
        txn = [e for e in new_entries if isinstance(e, data.Transaction)][-1]
        accounts = [p.account for p in txn.postings]
        self.assertIn("Income:Capital-Gains", accounts)
        self.assertFalse(any(":Short" in a or ":Long" in a for a in accounts))
