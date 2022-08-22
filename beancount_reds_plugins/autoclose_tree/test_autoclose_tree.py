import unittest
import re

import beancount_reds_plugins.autoclose_tree.autoclose_tree as autoclose_tree
from beancount.core import data
from beancount.parser import options
from beancount import loader

def s(e):
    return sorted(e, key=lambda x: (x.date, x.account))


class TestCloseAccountTree(unittest.TestCase):
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
        for a, e in zip(s(actual), s(expected)):
            self.assertEqual(a.date, e.date)
            self.assertEqual(a.account, e.account)

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
        for a, e in zip(s(actual), s(expected)):
            self.assertEqual(a.date, e.date)
            self.assertEqual(a.account, e.account)

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
        for a, e in zip(s(actual), s(expected)):
            self.assertEqual(a.date, e.date)
            self.assertEqual(a.account, e.account)

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
        self.assertEqual(len(actual), len(expected))
        for a, e in zip(s(actual), s(expected)):
            self.assertEqual(a.date, e.date)
            self.assertEqual(a.account, e.account)

    def test_match(self):
        entries, _, _ = loader.load_string("""
            2017-11-10 open Liabilities:Credit-Cards:Wife:Citi
            2017-11-10 open Liabilities:Credit-Cards:Wife:Citi-CustomCash
            2017-11-10 open Liabilities:Credit-Cards:Wife:Citi:Addon
            2018-11-10 close Liabilities:Credit-Cards:Wife:Citi
        """, dedent=True)

        expected, _, _ = loader.load_string("""
            2017-11-10 open Liabilities:Credit-Cards:Wife:Citi
            2017-11-10 open Liabilities:Credit-Cards:Wife:Citi-CustomCash
            2017-11-10 open Liabilities:Credit-Cards:Wife:Citi:Addon
            2018-11-10 close Liabilities:Credit-Cards:Wife:Citi
            2018-11-10 close Liabilities:Credit-Cards:Wife:Citi:Addon
        """, dedent=True)

        actual, _ = autoclose_tree.autoclose_tree(entries, {})
        self.assertEqual(len(actual), len(expected))
        for a, e in zip(s(actual), s(expected)):
            self.assertEqual(a.date, e.date)
            self.assertEqual(a.account, e.account)

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
        self.assertEqual(len(actual), len(expected))
        for a, e in zip(s(actual), s(expected)):
            self.assertEqual(a.date, e.date)
            self.assertEqual(a.account, e.account)
