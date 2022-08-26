"""See accompanying README.md"""

import re
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

    renames = dict([(re.compile(pattern), replacement)
                    for pattern, replacement in literal_eval(config).items()])

    def rename_account(account):
        """Apply 'renames' to 'account'.

        Return the resulting account name and whether or not it was renamed.

        """
        nonlocal rename_count
        was_renamed = False
        for pattern, replacement in renames.items():
            account, num_replacements = pattern.subn(replacement, account)
            if num_replacements > 0:
                rename_count += 1
                was_renamed = True
        return account, was_renamed

    def rename_account_in_entry(entry, account_attr='account'):
        """Apply 'renames' to 'getattr(entry, account_attr)'.

        Return the resulting entry and whether or not it was renamed.

        """
        old_account = getattr(entry, account_attr)
        new_account, was_renamed = rename_account(old_account)
        new_entry = entry._replace(**{account_attr: new_account}) if was_renamed else entry
        return new_entry, was_renamed

    for entry in entries:
        if isinstance(entry, data.Transaction):
            new_postings = []
            any_posting_changed = False
            for posting in entry.postings:
                new_posting, was_renamed = rename_account_in_entry(posting)
                any_posting_changed = any_posting_changed or was_renamed
                new_postings.append(new_posting)
            new_entry = entry._replace(postings=new_postings) if any_posting_changed else entry
        elif isinstance(entry, data.Pad):
            new_entry, _ = rename_account_in_entry(entry, 'account')
            new_entry, _ = rename_account_in_entry(new_entry, 'source_account')
        elif hasattr(entry, 'account'):
            new_entry, _ = rename_account_in_entry(entry)
        else:
            new_entry = entry

        new_entries.append(new_entry)

    if DEBUG:
        elapsed_time = time.time() - start_time
        print("Rename accounts [{:.2f}s]: {} postings renamed.".format(elapsed_time, rename_count))
    return new_entries, errors
