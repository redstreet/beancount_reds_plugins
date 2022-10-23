import unittest

import beancount_reds_plugins.opengroup.opengroup as opengroup
from beancount.parser import options
from beancount import loader


ruleset = "{}"

def s(e):
    return sorted(e, key=lambda x: (x.date, getattr(x, 'account', 'XXX')))


class Testopengroup(unittest.TestCase):
    def compare_opens(self, a, b):
        self.assertEqual(len(a), len(b))
        for i, j in zip(s(a), s(b)):
            self.assertEqual(i.date,       j.date)
            self.assertEqual(i.account,    j.account)
            self.assertEqual(i.currencies, i.currencies)
            self.assertEqual(i.booking,    j.booking)

    def test_empty_entries(self):
        new_entries, _ = opengroup.opengroup([], options.OPTIONS_DEFAULTS.copy(), ruleset)
        self.assertEqual([], new_entries)

    def test_basic(self):
        entries, _, _ = loader.load_string("""
            2000-01-01 open Assets:Investments:Taxable:Midelity PARENT
              opengroup_commodity_leaves: "ABC,DEFGH"
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
        self.compare_opens(actual, expected)

    def test_ticker(self):
        entries, _, _ = loader.load_string("""
            2000-01-01 open Assets:Investments:Taxable:Midelity PARENT
              opengroup_commodity_leaves_default_booking: "ABC,DEFGH"
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
        self.compare_opens(actual, expected)

    def test_rule_fifo(self):
        entries, _, _ = loader.load_string("""
            2000-01-01 open Assets:Investments:Taxable:Midelity PARENT
              opengroup_commodity_leaves: "ABC"
        """, dedent=True)

        expected, _, _ = loader.load_string("""
            2000-01-01 open Assets:Investments:Taxable:Midelity PARENT

            2000-01-01 open Income:Investments:Taxable:Capital-Gains:Midelity:ABC   USD
            2000-01-01 open Income:Investments:Taxable:Dividends:Midelity:ABC       USD
            2000-01-01 open Income:Investments:Taxable:Interest:Midelity:ABC       USD
        """, dedent=True)

        actual, _ = opengroup.opengroup(entries, {}, ruleset)
        self.compare_opens(actual, expected)
