"""See accompanying README.md"""

import time
from ast import literal_eval
from beancount.core import data

DEBUG = 0
__plugins__ = ('rename_accounts',)


def rename_accounts(entries, options_map, config):  # noqa: C901
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

    def rename_account_in_entry(entry, account_attr='account'):
        old_account = getattr(entry, account_attr)
        new_account = rename_account(old_account)
        if new_account is not old_account:
            return entry._replace(**{account_attr: new_account})
        else:
            return entry

    for entry in entries:
        if isinstance(entry, data.Transaction):
            new_postings = []
            any_posting_changed = False
            for posting in entry.postings:
                new_posting = rename_account_in_entry(posting)
                if new_posting is not posting:
                    any_posting_changed = True
                new_postings.append(new_posting)
            if any_posting_changed:
                new_entry = entry._replace(postings=new_postings)
            else:
                new_entry = entry
        elif isinstance(entry, data.Pad):
            new_entry = rename_account_in_entry(entry, 'account')
            new_entry = rename_account_in_entry(new_entry, 'source_account')
        elif hasattr(entry, 'account'):
            new_entry = rename_account_in_entry(entry)
        else:
            new_entry = entry

        new_entries.append(new_entry)

    if DEBUG:
        elapsed_time = time.time() - start_time
        print("Rename accounts [{:.2f}s]: {} postings renamed.".format(elapsed_time, rename_count))
    return new_entries, errors
