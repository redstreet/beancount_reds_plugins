import beancount_reds_plugins.autoclose_tree.autoclose_tree as autoclose_tree
from beancount.parser import options
from beancount import loader
from beancount.parser import cmptest


class TestCloseTree(cmptest.TestCase):
    def test_empty_entries(self):
        new_entries, _ = autoclose_tree.autoclose_tree([], options.OPTIONS_DEFAULTS.copy())
        self.assertEqual([], new_entries)

    def test_basic(self):
        entries, _, _ = loader.load_string("""
            2014-01-01 open Assets:XBank
            2014-01-01 open Assets:XBank:AAPL
            2015-01-01 close Assets:XBank
        """, dedent=True)

        expected, _, _ = loader.load_string("""
            2014-01-01 open Assets:XBank
            2014-01-01 open Assets:XBank:AAPL
            2015-01-01 close Assets:XBank
            2015-01-01 close Assets:XBank:AAPL
        """, dedent=True)

        actual, _ = autoclose_tree.autoclose_tree(entries, {})
        self.assertEqualEntries(actual, expected)

    def test_leave_others_untouched(self):
        entries, _, _ = loader.load_string("""
            2014-01-01 open Assets:YBank
            2014-01-01 open Assets:YBank:AAPL
            2014-01-01 open Assets:XBank
            2014-01-01 open Assets:XBank:AAPL
            2014-01-01 open Assets:XBank:AAPL:Fuji
            2014-01-01 open Assets:XBank:AAPL:Gala
            2014-01-01 open Assets:XBank:ORNG
            2014-01-01 open Assets:XBank:BANANA
            2015-01-01 close Assets:XBank
        """, dedent=True)

        expected, _, _ = loader.load_string("""
            2014-01-01 open Assets:YBank
            2014-01-01 open Assets:YBank:AAPL
            2014-01-01 open Assets:XBank
            2014-01-01 open Assets:XBank:AAPL
            2014-01-01 open Assets:XBank:AAPL:Fuji
            2014-01-01 open Assets:XBank:AAPL:Gala
            2014-01-01 open Assets:XBank:ORNG
            2014-01-01 open Assets:XBank:BANANA
            2015-01-01 close Assets:XBank
            2015-01-01 close Assets:XBank:AAPL
            2015-01-01 close Assets:XBank:AAPL:Fuji
            2015-01-01 close Assets:XBank:AAPL:Gala
            2015-01-01 close Assets:XBank:ORNG
            2015-01-01 close Assets:XBank:BANANA
        """, dedent=True)

        actual, _ = autoclose_tree.autoclose_tree(entries, {})
        self.assertEqualEntries(actual, expected)

    def test_override(self):
        entries, _, _ = loader.load_string("""
            2014-01-01 open Assets:XBank
            2014-01-01 open Assets:XBank:AAPL
            2014-01-01 open Assets:XBank:AAPL:Fuji
            2015-01-01 close Assets:XBank:AAPL:Fuji
            2016-01-01 close Assets:XBank
        """, dedent=True)

        expected, _, _ = loader.load_string("""
            2014-01-01 open Assets:XBank
            2014-01-01 open Assets:XBank:AAPL
            2014-01-01 open Assets:XBank:AAPL:Fuji
            2015-01-01 close Assets:XBank:AAPL:Fuji
            2016-01-01 close Assets:XBank
            2016-01-01 close Assets:XBank:AAPL
        """, dedent=True)

        actual, _ = autoclose_tree.autoclose_tree(entries, {})
        self.assertEqualEntries(actual, expected)

    def test_override_complex(self):
        entries, _, _ = loader.load_string("""
            2014-01-01 open Assets:XBank
            2014-01-01 open Assets:XBank:AAPL
            2014-01-01 open Assets:XBank:AAPL:Fuji
            2015-01-01 close Assets:XBank:AAPL
            2016-01-01 close Assets:XBank
        """, dedent=True)

        expected, _, _ = loader.load_string("""
            2014-01-01 open Assets:XBank
            2014-01-01 open Assets:XBank:AAPL
            2014-01-01 open Assets:XBank:AAPL:Fuji

            2015-01-01 close Assets:XBank:AAPL
            2015-01-01 close Assets:XBank:AAPL:Fuji

            2016-01-01 close Assets:XBank
        """, dedent=True)

        actual, _ = autoclose_tree.autoclose_tree(entries, {})
        self.assertEqualEntries(actual, expected)

    def test_match(self):
        entries, _, _ = loader.load_string("""
            2017-11-10 open Liabilities:Credit-Cards:Spouse:Citi
            2017-11-10 open Liabilities:Credit-Cards:Spouse:Citi-CustomCash
            2017-11-10 open Liabilities:Credit-Cards:Spouse:Citi:Addon
            2018-11-10 close Liabilities:Credit-Cards:Spouse:Citi
        """, dedent=True)

        expected, _, _ = loader.load_string("""
            2017-11-10 open Liabilities:Credit-Cards:Spouse:Citi
            2017-11-10 open Liabilities:Credit-Cards:Spouse:Citi-CustomCash
            2017-11-10 open Liabilities:Credit-Cards:Spouse:Citi:Addon
            2018-11-10 close Liabilities:Credit-Cards:Spouse:Citi
            2018-11-10 close Liabilities:Credit-Cards:Spouse:Citi:Addon
        """, dedent=True)

        actual, _ = autoclose_tree.autoclose_tree(entries, {})
        self.assertEqualEntries(actual, expected)

    def test_close_unopened_parent(self):
        entries, _, _ = loader.load_string("""
            2017-11-10 open Assets:Brokerage:AAPL
            2017-11-10 open Assets:Brokerage:ORNG
            2018-11-10 close Assets:Brokerage
        """, dedent=True)

        expected, _, _ = loader.load_string("""
            2017-11-10 open Assets:Brokerage:AAPL
            2017-11-10 open Assets:Brokerage:ORNG
            2018-11-10 close Assets:Brokerage:AAPL
            2018-11-10 close Assets:Brokerage:ORNG
        """, dedent=True)

        actual, _ = autoclose_tree.autoclose_tree(entries, {})
        self.assertEqualEntries(actual, expected)

    def test_auto_accounts_parent_close(self):
        entries, _, _ = loader.load_string("""
            plugin "beancount.plugins.auto_accounts"

            2019-01-01 * "Transaction"
              Expenses:Non-Retirement:Auto:Fit:Insurance   -10 USD
              Expenses:Non-Retirement:Auto:Fit:Gas

            2021-06-17 close Expenses:Non-Retirement:Auto:Fit
        """, dedent=True)

        expected, _, _ = loader.load_string("""
            2019-01-01 open Expenses:Non-Retirement:Auto:Fit:Insurance
            2019-01-01 open Expenses:Non-Retirement:Auto:Fit:Gas

            2019-01-01 * "Transaction"
              Expenses:Non-Retirement:Auto:Fit:Insurance   -10 USD
              Expenses:Non-Retirement:Auto:Fit:Gas

            2021-06-17 open Expenses:Non-Retirement:Auto:Fit
            2021-06-17 close Expenses:Non-Retirement:Auto:Fit:Insurance
            2021-06-17 close Expenses:Non-Retirement:Auto:Fit:Gas
            2021-06-17 close Expenses:Non-Retirement:Auto:Fit
        """, dedent=True)

        actual, _ = autoclose_tree.autoclose_tree(entries, {})
        self.assertEqualEntries(actual, expected)
