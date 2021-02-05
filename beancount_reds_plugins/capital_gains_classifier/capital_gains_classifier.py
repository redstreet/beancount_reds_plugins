"""See accompanying README.md"""

import re
import time

from beancount.core import data
from beancount.core import getters
from ast import literal_eval

DEBUG = 0

__plugins__ = ('capital_gains_classifier',)


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


def capital_gains_classifier(entries, options_map, config):
    """Insert entries for unmatched transactions in zero-sum accounts.

    Args:
      entries: a list of entry instances

      options_map: a dict of options parsed from the file (not used)

      config: A configuration string, which is intended to be a Python dict
      listing rewrites. Eg: "{'Expenses:Taxes' : 'Income:Taxes'}"

     "Income.*Capital-Gains:Long:.*",  ":Long:",  ":Long:Losses:",  ":Long:Gains:"
     "Income.*Capital-Gains:Short:.*, ":Short:, ":Short:Losses:, ":Short:Gains:"

    Returns:
      A tuple of entries and errors. """

    start_time = time.time()
    rewrite_count = 0
    new_accounts = []
    errors = []

    rewrites = literal_eval(config)  # TODO: error check

    for entry in entries:
        if isinstance(entry, data.Transaction):
            # matched = False
            postings = list(entry.postings)
            for posting in postings:
                account = posting.account
                if any(re.match(r, account) for r in rewrites):
                    # matched = True
                    for r in rewrites:
                        if posting.units.number < 0:
                            account = account.replace(rewrites[r][0], rewrites[r][1])  # losses
                        else:
                            account = account.replace(rewrites[r][0], rewrites[r][2])  # gains
                        rewrite_count += 1
                        if account not in new_accounts:
                            new_accounts.append(account)
                    account_replace(entry, posting, account)
            # if matched:
            #     for posting in postings:
            #         account = posting.account

    new_open_entries = create_open_directives(new_accounts, entries)
    if DEBUG:
        elapsed_time = time.time() - start_time
        print("Capital gains classifier [{:.1f}s]: {} postings classified.".format(elapsed_time, rewrite_count))
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
