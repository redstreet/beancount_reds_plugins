"""See accompanying README.md"""

import time
from ast import literal_eval
from beancount.core import data

DEBUG = 0
__plugins__ = ('rename_accounts',)


def rename_accounts(entries, options_map, config):
    """Insert entries for unmatched transactions in zero-sum accounts.

    Args:
      entries: a list of entry instances

      options_map: a dict of options parsed from the file (not used)

      config: A configuration string, which is intended to be a Python dict
      listing renames. Eg: "{'Expenses:Taxes' : 'Income:Taxes'}"

    Returns:
      A tuple of entries and errors. """

    start_time = time.time()
    rename_count = 0
    new_entries = []
    errors = []

    renames = literal_eval(config)

    def rename_account(account):
        """Apply 'renames' to 'account' and return the resulting account name."""
        nonlocal rename_count
        for r in renames:
            if r in account:
                account = account.replace(r, renames[r])
                rename_count += 1
        return account

    for entry in entries:
        if isinstance(entry, data.Transaction):
            new_postings = []
            for posting in entry.postings:
                new_postings.append(posting._replace(account=rename_account(posting.account)))
            new_entry = entry._replace(postings=new_postings)
        elif isinstance(entry, data.Pad):
            new_entry = entry._replace(account=rename_account(entry.account),
                                       source_account=rename_account(entry.source_account))
        elif hasattr(entry, 'account'):
            new_entry = entry._replace(account=rename_account(entry.account))
        else:
            new_entry = entry

        new_entries.append(new_entry)

    if DEBUG:
        elapsed_time = time.time() - start_time
        print("Rename accounts [{:.2f}s]: {} postings renamed.".format(elapsed_time, rename_count))
    return new_entries, errors
