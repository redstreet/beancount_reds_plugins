import unittest
import re

# from beancount.plugins import unrealized
import beancount_reds_plugins.zerosum.zerosum as zerosum
from beancount.core import data
from beancount.parser import options
from beancount import loader

config = """{
 'zerosum_accounts' : { 
 'Assets:Zero-Sum-Accounts:Returns-and-Temporary'              : ('', 90),
  },
  'account_name_replace' : ('Zero-Sum-Accounts', 'ZSA-Matched')
 }"""

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


class TestUnrealized(unittest.TestCase):

    def test_empty_entries(self):
        new_entries, _ = zerosum.zerosum([], options.OPTIONS_DEFAULTS.copy(), "{}")
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
        new_entries, _ = zerosum.zerosum(entries, options_map, "{}")
        self.assertEqual(new_entries, entries)

    @loader.load_doc()
    def test_single_rename(self, entries, _, options_map):
        """
        2015-01-01 open Liabilities:Credit-Cards:Visa
        2015-01-01 open Assets:Zero-Sum-Accounts:Returns-and-Temporary
        2015-06-15 * "Expensive furniture"
          Liabilities:Credit-Cards:Visa  -2526.02 USD
          Assets:Zero-Sum-Accounts:Returns-and-Temporary             1263.01 USD
          Assets:Zero-Sum-Accounts:Returns-and-Temporary             1263.01 USD
        
        2015-06-23 * "Expensive furniture Refund"
          Liabilities:Credit-Cards:Visa  1263.01 USD
          Assets:Zero-Sum-Accounts:Returns-and-Temporary
        
        2015-06-23 * "Expensive furniture Refund"
          Liabilities:Credit-Cards:Visa  1263.01 USD
          Assets:Zero-Sum-Accounts:Returns-and-Temporary
        """
        new_entries, _ = zerosum.zerosum(entries, options_map, config)

        matched = get_entries_with_acc_regexp(new_entries, ':ZSA-Matched')
        self.assertEqual(3, len(matched))

        ref = [(0, 1), (0, 2), (1, 1), (2, 1)]

        for (m, p) in ref:
            self.assertEqual('Assets:ZSA-Matched:Returns-and-Temporary', matched[m].postings[p].account)

    @loader.load_doc()
    def test_above_epsilon(self, entries, _, options_map):
        """
        2015-01-01 open Liabilities:Credit-Cards:Visa
        2015-01-01 open Assets:Zero-Sum-Accounts:Returns-and-Temporary
        2015-06-15 * "Trinket"
          Liabilities:Credit-Cards:Visa  -0.014 USD
          Assets:Zero-Sum-Accounts:Returns-and-Temporary
        
        2015-06-23 * "Trinket refund"
          Liabilities:Credit-Cards:Visa  0.014 USD
          Assets:Zero-Sum-Accounts:Returns-and-Temporary
        """
        new_entries, _ = zerosum.zerosum(entries, options_map, config)

        matched = get_entries_with_acc_regexp(new_entries, ':ZSA-Matched')
        self.assertEqual(2, len(matched))

        ref = [(0, 1), (1, 1)]

        for (m, p) in ref:
            self.assertEqual('Assets:ZSA-Matched:Returns-and-Temporary', matched[m].postings[p].account)

    @loader.load_doc()
    def test_below_epsilon(self, entries, _, options_map):
        """
        2015-01-01 open Liabilities:Credit-Cards:Visa
        2015-01-01 open Assets:Zero-Sum-Accounts:Returns-and-Temporary
        2015-06-15 * "Trinket"
          Liabilities:Credit-Cards:Visa  -0.004 USD
          Assets:Zero-Sum-Accounts:Returns-and-Temporary
        
        2015-06-23 * "Trinket refund"
          Liabilities:Credit-Cards:Visa  0.004 USD
          Assets:Zero-Sum-Accounts:Returns-and-Temporary
        """
        new_entries, _ = zerosum.zerosum(entries, options_map, config)

        matched = get_entries_with_acc_regexp(new_entries, ':ZSA-Matched')
        self.assertEqual(2, len(matched))

        ref = [(0, 1), (1, 1)]

        for (m, p) in ref:
            self.assertEqual('Assets:ZSA-Matched:Returns-and-Temporary', matched[m].postings[p].account)

    @loader.load_doc()
    def test_lookalike(self, entries, _, options_map):
        """
        2015-01-01 open Liabilities:Credit-Cards:Visa
        2015-01-01 open Assets:Zero-Sum-Accounts:Returns-and-Temporary

        2020-06-01 * "Match two lookalike postings in one txn" ; should not error
          Assets:Zero-Sum-Accounts:Returns-and-Temporary  0.00 USD
          Assets:Zero-Sum-Accounts:Returns-and-Temporary  0.00 USD
        """
        new_entries, _ = zerosum.zerosum(entries, options_map, config)

        matched = get_entries_with_acc_regexp(new_entries, ':ZSA-Matched')
        self.assertEqual(1, len(matched))

        ref = [(0, 0), (0, 1)]

        for (m, p) in ref:
            self.assertEqual('Assets:ZSA-Matched:Returns-and-Temporary', matched[m].postings[p].account)

    @loader.load_doc()
    def test_both_postings_in_one_txn(self, entries, _, options_map):
        """
        2015-01-01 open Liabilities:Credit-Cards:Visa
        2015-01-01 open Assets:Zero-Sum-Accounts:Returns-and-Temporary

        2020-01-01 * "Match both postings in one txn"
          Assets:Zero-Sum-Accounts:Returns-and-Temporary -1.00 USD
          Assets:Zero-Sum-Accounts:Returns-and-Temporary  1.00 USD
        """
        new_entries, _ = zerosum.zerosum(entries, options_map, config)

        matched = get_entries_with_acc_regexp(new_entries, ':ZSA-Matched')
        self.assertEqual(1, len(matched))

        ref = [(0, 0), (0, 1)]

        for (m, p) in ref:
            self.assertEqual('Assets:ZSA-Matched:Returns-and-Temporary', matched[m].postings[p].account)


