import unittest
import re

# from beancount.plugins import unrealized
import beancount_reds_plugins.rename_accounts.rename_accounts as rename_accounts
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


class TestUnrealized(unittest.TestCase):

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

        renamed = get_entries_with_acc_regexp(new_entries, ':Taxes')
        self.assertEqual(1, len(renamed))
        self.assertEqual('Income:Taxes', renamed[0].postings[1].account)
