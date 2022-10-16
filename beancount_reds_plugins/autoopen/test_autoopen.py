import unittest

import beancount_reds_plugins.autoopen.autoopen as autoopen
from beancount.parser import options
from beancount import loader


def s(e):
    return sorted(e, key=lambda x: (x.date, getattr(x, 'account', 'XXX')))


class TestAutoOpen(unittest.TestCase):
    def test_empty_entries(self):
        new_entries, _ = autoopen.autoopen([], options.OPTIONS_DEFAULTS.copy())
        self.assertEqual([], new_entries)

    def test_basic(self):
        entries, _, _ = loader.load_string("""
            2000-01-01 open Assets:Investments:Taxable:Midelity PARENT
              autoopen_commodity_leaves_strict: "ABC,DEFGH"
        """, dedent=True)

        expected, _, _ = loader.load_string("""
            2000-01-01 open Assets:Investments:Taxable:Midelity PARENT

            2000-01-01 open Assets:Investments:Taxable:Midelity:ABC                 "STRICT"
            2000-01-01 open Income:Investments:Taxable:Capital-Gains:Midelity:ABC   USD
            2000-01-01 open Income:Investments:Taxable:Dividends:Midelity:ABC       USD
            2000-01-01 open Income:Investments:Taxable:Interest:Midelity:ABC       USD

            2000-01-01 open Assets:Investments:Taxable:Midelity:DEFGH                 "STRICT"
            2000-01-01 open Income:Investments:Taxable:Capital-Gains:Midelity:DEFGH   USD
            2000-01-01 open Income:Investments:Taxable:Dividends:Midelity:DEFGH       USD
            2000-01-01 open Income:Investments:Taxable:Interest:Midelity:DEFGH       USD
        """, dedent=True)

        actual, _ = autoopen.autoopen(entries, {})
        self.assertEqual(len(actual), len(expected))
        for a, e in zip(s(actual), s(expected)):
            self.assertEqual(a.date, e.date)
            self.assertEqual(a.account, e.account)

    def test_rule_fifo(self):
        entries, _, _ = loader.load_string("""
            2000-01-01 open Assets:Investments:Taxable:Midelity PARENT
              autoopen_commodity_leaves_fifo: "ABC"
        """, dedent=True)

        expected, _, _ = loader.load_string("""
            2000-01-01 open Assets:Investments:Taxable:Midelity PARENT

            2000-01-01 open Assets:Investments:Taxable:Midelity:ABC                 "FIFO"
            2000-01-01 open Income:Investments:Taxable:Capital-Gains:Midelity:ABC   USD
            2000-01-01 open Income:Investments:Taxable:Dividends:Midelity:ABC       USD
            2000-01-01 open Income:Investments:Taxable:Interest:Midelity:ABC       USD
        """, dedent=True)

        actual, _ = autoopen.autoopen(entries, {})
        self.assertEqual(len(actual), len(expected))
        for a, e in zip(s(actual), s(expected)):
            self.assertEqual(a.date, e.date)
            self.assertEqual(a.account, e.account)
