"""See accompanying README.md"""

import time

from ast import literal_eval
from beancount.core import data
from beancount_reds_plugins.common import common

DEBUG = 0

__plugins__ = ('rename_accounts',)


def pretty_print_transaction(t):
    print(t.date)
    for p in t.postings:
        print("            ", p.account, p.position)
    print("")


# replace the account on a given posting with a new account
def account_replace(txn, posting, new_account):
    # create a new posting with the new account, then remove old and add new
    # from parent transaction
    new_posting = posting._replace(account=new_account)
    txn.postings.remove(posting)
    txn.postings.append(new_posting)


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
    new_accounts = []
    errors = []

    renames = literal_eval(config)  # TODO: error check

    for entry in entries:
        if isinstance(entry, data.Transaction):
            postings = list(entry.postings)
            for posting in postings:
                account = posting.account
                if any(r in account for r in renames):
                    for r in renames:
                        account = account.replace(r, renames[r])
                        rename_count += 1
                        if account not in new_accounts:
                            new_accounts.append(account)
                    account_replace(entry, posting, account)

    new_open_entries = common.create_open_directives(new_accounts, entries, meta_desc='<rename_accounts>')
    if DEBUG:
        elapsed_time = time.time() - start_time
        print("Rename accounts [{:.1f}s]: {} postings renamed.".format(elapsed_time, rename_count))
    return new_open_entries + entries, errors
