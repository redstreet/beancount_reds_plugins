import beancount_reds_plugins.rename_accounts.rename_accounts as rename_accounts
from beancount.parser import options
from beancount import loader
from beancount.parser import cmptest


class TestUnrealized(cmptest.TestCase):

    def test_empty_entries(self):
        new_entries, _ = rename_accounts.rename_accounts([], options.OPTIONS_DEFAULTS.copy(), "{}")
        self.assertEqual([], new_entries)

    @loader.load_doc()
    def test_empty_config(self, entries, _, options_map):
        """
        2014-01-01 open Assets:Account1
        2014-01-01 open Assets:Account2
        2014-01-01 open Income:Misc

        2014-01-15 *
          Income:Misc           -1000 USD
          Assets:Account1

        2014-01-16 *
          Income:Misc           -1000 EUR
          Assets:Account2
        """
        new_entries, _ = rename_accounts.rename_accounts(entries, options_map, "{}")
        self.assertEqual(new_entries, entries)

    @loader.load_doc()
    def test_single_rename(self, entries, _, options_map):
        """
        2014-01-01 open Assets:Account1
        2014-01-01 open Assets:Account2
        2014-01-01 open Expenses:Taxes

        2014-01-15 *
          Assets:Account1
          Assets:Account2 -1000 USD

        2014-01-16 *
          Assets:Account2
          Expenses:Taxes          1000 USD
        """
        config = "{'Expenses:Taxes' : 'Income:Taxes'}"
        new_entries, _ = rename_accounts.rename_accounts(entries, options_map, config)

        self.assertEqualEntries("""
        2014-01-01 open Assets:Account1
        2014-01-01 open Assets:Account2
        2014-01-01 open Income:Taxes

        2014-01-15 *
          Assets:Account1  1000 USD
          Assets:Account2 -1000 USD

        2014-01-16 *
          Assets:Account2      -1000 USD
          Income:Taxes          1000 USD
        """, new_entries)

    @loader.load_doc()
    def test_all_directives(self, entries, _, options_map):
        """
            2014-01-01 open Assets:Account1
            2014-01-01 open Assets:Account2
            2014-01-01 open Equity:Opening-Balances

            2014-01-01 commodity AAPL
              price: "USD:yahoo/AAPL"

            2014-01-14 pad Assets:Account1 Equity:Opening-Balances

            2014-01-15 balance Assets:Account1 1000 USD

            2014-01-16 * "Buy AAPL"
              Assets:Account1        -1000 USD
              Assets:Account2         1 AAPL {1000 USD}

            2014-01-16 price AAPL 1000 USD

            2014-01-17 * "Sell AAPL"
              Assets:Account2        -1 AAPL {1000 USD}
              Assets:Account1          1000 USD

            2014-01-18 note Assets:Account1 "Test note"

            2014-12-31 close Assets:Account1

            2014-12-31 event "location" "Paris, France"

            2014-12-31 query "france-balances" "
              SELECT account, sum(position) WHERE ‘trip-france-2014’ in tags"

            2014-12-31 custom "budget" "..." TRUE 45.30 USD
        """

        config = """{
            'Assets:Account1': 'Assets:Cash',
            'Assets:Account2': 'Assets:AAPL',
            'Equity:Opening-Balances': 'Equity:OpeningBalances',
        }"""
        new_entries, _ = rename_accounts.rename_accounts(entries, options_map, config)

        self.assertEqualEntries("""
            2014-01-01 open Assets:Cash
            2014-01-01 open Assets:AAPL
            2014-01-01 open Equity:OpeningBalances

            2014-01-01 commodity AAPL
              price: "USD:yahoo/AAPL"

            2014-01-14 pad Assets:Cash Equity:OpeningBalances

            2014-01-14 P "(Padding inserted for Balance of 1000 USD for difference 1000 USD)"
             Assets:Cash              1000 USD
             Equity:OpeningBalances  -1000 USD

            2014-01-15 balance Assets:Cash 1000 USD

            2014-01-16 * "Buy AAPL"
              Assets:AAPL         1 AAPL {1000 USD}
              Assets:Cash        -1000 USD

            2014-01-16 price AAPL 1000 USD

            2014-01-17 * "Sell AAPL"
              Assets:AAPL        -1 AAPL {1000 USD}
              Assets:Cash          1000 USD

            2014-01-18 note Assets:Cash "Test note"

            2014-12-31 close Assets:Cash

            2014-12-31 event "location" "Paris, France"

            2014-12-31 query "france-balances" "
              SELECT account, sum(position) WHERE ‘trip-france-2014’ in tags"

            2014-12-31 custom "budget" "..." TRUE 45.30 USD
        """, new_entries)

    @loader.load_doc()
    def test_regex_rename(self, entries, _, options_map):
        """
            2014-01-01 open Assets:Checking USD
            2014-01-01 open Assets:Brokerage:Cash USD
            2014-01-01 open Assets:Brokerage:VTI VTI
            2014-01-01 open Assets:Brokerage:BND BND
            2014-01-01 open Income:Brokerage:Dividends:VTI USD
            2014-01-01 open Income:Brokerage:Dividends:BND USD
            2014-01-01 open Expenses:Brokerage:Fees USD

            2014-01-15 * "Bank transfer"
              Assets:Checking -1000 USD
              Assets:Brokerage:Cash 1000 USD

            2014-01-15 * "Buy stock"
              Assets:Brokerage:Cash -500 USD
              Assets:Brokerage:VTI 5 VTI {{500 USD}}

            2014-01-15 * "Buy stock"
              Assets:Brokerage:Cash -500 USD
              Assets:Brokerage:BND 10 BND {{500 USD}}

            2014-01-16 * "Dividend"
              Income:Brokerage:Dividends:VTI -5 USD
              Assets:Brokerage:Cash 5 USD

            2014-01-16 * "Dividend"
              Income:Brokerage:Dividends:BND -25 USD
              Assets:Brokerage:Cash 25 USD

            2014-01-17 * "Fees"
              Assets:Brokerage:Cash -10 USD
              Expenses:Brokerage:Fees 10 USD
        """

        config = r"""{
            'Income(:.+)?:Dividends(:.+)?' : 'Assets\\1:Dividends\\2',
            'Expenses(:.+)?:Fees(:.+)?' : 'Assets\\1:Fees\\2',
        }"""
        new_entries, _ = rename_accounts.rename_accounts(entries, options_map, config)

        self.assertEqualEntries("""
            2014-01-01 open Assets:Checking USD
            2014-01-01 open Assets:Brokerage:Cash USD
            2014-01-01 open Assets:Brokerage:VTI VTI
            2014-01-01 open Assets:Brokerage:BND BND
            2014-01-01 open Assets:Brokerage:Dividends:VTI USD
            2014-01-01 open Assets:Brokerage:Dividends:BND USD
            2014-01-01 open Assets:Brokerage:Fees USD

            2014-01-15 * "Bank transfer"
              Assets:Checking -1000 USD
              Assets:Brokerage:Cash 1000 USD

            2014-01-15 * "Buy stock"
              Assets:Brokerage:Cash -500 USD
              Assets:Brokerage:VTI 5 VTI {{500 USD}}

            2014-01-15 * "Buy stock"
              Assets:Brokerage:Cash -500 USD
              Assets:Brokerage:BND 10 BND {{500 USD}}

            2014-01-16 * "Dividend"
              Assets:Brokerage:Dividends:VTI -5 USD
              Assets:Brokerage:Cash 5 USD

            2014-01-16 * "Dividend"
              Assets:Brokerage:Dividends:BND -25 USD
              Assets:Brokerage:Cash 25 USD

            2014-01-17 * "Fees"
              Assets:Brokerage:Cash -10 USD
              Assets:Brokerage:Fees 10 USD
        """, new_entries)
