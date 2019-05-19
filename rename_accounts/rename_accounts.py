"""See accompanying README.md"""

import collections
import time

from beancount.core.amount import ZERO
from beancount.core import data
from beancount.core import account
from beancount.core import getters
from beancount.core import position
from beancount.core import flags
from beancount.ops import holdings
from beancount.parser import options
from beancount.parser import printer

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
      mapping zerosum account name -> (matched zerosum account name,
      date_range). See example for more info.

    Returns:
      A tuple of entries and errors. """

    start_time = time.time()
    rename_count = 0
    new_accounts = []
    errors = []


    for entry in entries:
        if isinstance(entry, data.Transaction):
            postings = list(entry.postings)
            for posting in postings:
                if 'Expenses:Taxes' in posting.account:
                    acc = posting.account.replace("Expenses", "Income")
                    account_replace(entry, posting, acc)
                    rename_count += 1
                    if acc not in new_accounts:
                        new_accounts.append(acc)

    new_open_entries = create_open_directives(new_accounts, entries)
    if DEBUG:
        elapsed_time = time.time() - start_time
        print("Rename accounts [{:.1f}s]: {} postings renamed.".format(elapsed_time, rename_count))
    return(new_open_entries + entries, errors)



def create_open_directives(new_accounts, entries):
    meta = data.new_metadata('<zerosum>', 0)
    # Ensure that the accounts we're going to use to book the postings exist, by
    # creating open entries for those that we generated that weren't already
    # existing accounts.
    earliest_date = entries[0].date
    open_entries = getters.get_account_open_close(entries)
    new_open_entries = []
    for account_ in sorted(new_accounts):
        if account_ not in open_entries:
            meta = data.new_metadata(meta['filename'], 0)
            open_entry = data.Open(meta, earliest_date, account_, None, None)
            new_open_entries.append(open_entry)
    return(new_open_entries)
