import beancount_reds_plugins.opengroup.opengroup as opengroup
from beancount.parser import options
from beancount import loader
from beancount.parser import cmptest


ruleset = "{}"


class Testopengroup(cmptest.TestCase):
    def test_empty_entries(self):
        new_entries, _ = opengroup.opengroup([], options.OPTIONS_DEFAULTS.copy(), ruleset)
        self.assertEqualEntries([], new_entries)

    def test_basic(self):
        entries, _, _ = loader.load_string("""
            2000-01-01 open Assets:Investments:Taxable:Midelity PARENT
              opengroup_commodity_leaves_income: "ABC,DEFGH"
        """, dedent=True)

        expected, _, _ = loader.load_string("""
            2000-01-01 open Assets:Investments:Taxable:Midelity PARENT

            2000-01-01 open Income:Investments:Taxable:Capital-Gains:Midelity:ABC   USD
            2000-01-01 open Income:Investments:Taxable:Dividends:Midelity:ABC       USD
            2000-01-01 open Income:Investments:Taxable:Interest:Midelity:ABC       USD

            2000-01-01 open Income:Investments:Taxable:Capital-Gains:Midelity:DEFGH   USD
            2000-01-01 open Income:Investments:Taxable:Dividends:Midelity:DEFGH       USD
            2000-01-01 open Income:Investments:Taxable:Interest:Midelity:DEFGH       USD
        """, dedent=True)

        actual, _ = opengroup.opengroup(entries, {}, ruleset)
        self.assertEqualEntries(actual, expected)

    def test_ticker(self):
        entries, _, _ = loader.load_string("""
            2000-01-01 open Assets:Investments:Taxable:Midelity PARENT
              opengroup_commodity_leaves_income_and_asset: "ABC,DEFGH"
        """, dedent=True)

        expected, _, _ = loader.load_string("""
            2000-01-01 open Assets:Investments:Taxable:Midelity PARENT

            2000-01-01 open Assets:Investments:Taxable:Midelity:ABC                 ABC
            2000-01-01 open Income:Investments:Taxable:Capital-Gains:Midelity:ABC   USD
            2000-01-01 open Income:Investments:Taxable:Dividends:Midelity:ABC       USD
            2000-01-01 open Income:Investments:Taxable:Interest:Midelity:ABC        USD

            2000-01-01 open Assets:Investments:Taxable:Midelity:DEFGH                 DEFGH
            2000-01-01 open Income:Investments:Taxable:Capital-Gains:Midelity:DEFGH   USD
            2000-01-01 open Income:Investments:Taxable:Dividends:Midelity:DEFGH       USD
            2000-01-01 open Income:Investments:Taxable:Interest:Midelity:DEFGH        USD
        """, dedent=True)

        actual, _ = opengroup.opengroup(entries, {}, ruleset)
        self.assertEqualEntries(actual, expected)

    def test_rule_fifo(self):
        entries, _, _ = loader.load_string("""
            2000-01-01 open Assets:Investments:Taxable:Midelity PARENT
              opengroup_commodity_leaves_income: "ABC"
        """, dedent=True)

        expected, _, _ = loader.load_string("""
            2000-01-01 open Assets:Investments:Taxable:Midelity PARENT

            2000-01-01 open Income:Investments:Taxable:Capital-Gains:Midelity:ABC   USD
            2000-01-01 open Income:Investments:Taxable:Dividends:Midelity:ABC       USD
            2000-01-01 open Income:Investments:Taxable:Interest:Midelity:ABC       USD
        """, dedent=True)

        actual, _ = opengroup.opengroup(entries, {}, ruleset)
        self.assertEqualEntries(actual, expected)
