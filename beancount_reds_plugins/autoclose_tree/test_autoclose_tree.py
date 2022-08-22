import unittest
import re

import beancount_reds_plugins.autoclose_tree.autoclose_tree as autoclose_tree
from beancount.core import data
from beancount.parser import options
from beancount import loader


def get_entries_with_acc_regexp(entries, regexp):
    print(regexp)
    return [entry
            for entry in entries
            if (isinstance(entry, data.Transaction) and
                any(re.search(regexp, posting.account) for posting in entry.postings))]


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


class TestCloseAccountTree(unittest.TestCase):

    def test_empty_entries(self):
        new_entries, _ = autoclose_tree.autoclose_tree([], options.OPTIONS_DEFAULTS.copy())
        self.assertEqual([], new_entries)

    def test_basic(self):
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
        for a, e in zip(actual, expected):
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
        for a, e in zip(actual, expected):
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

        def s(e):
            return sorted(e, key=lambda x: x.date)

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

        def s(e):
            return sorted(e, key=lambda x: x.date)

        actual, _ = autoclose_tree.autoclose_tree(entries, {})
        self.assertEqual(len(actual), len(expected))
        for a, e in zip(s(actual), s(expected)):
            self.assertEqual(a.date, e.date)
            self.assertEqual(a.account, e.account)
