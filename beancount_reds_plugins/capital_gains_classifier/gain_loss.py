"""Classifies and rebooks capital gains accounts into separate gains and losses accounts
"""

import re
import time
from beancount.core import data
from ast import literal_eval
from beancount_reds_plugins.common import common

DEBUG = 0
__plugins__ = ('gain_loss',)


def account_replace(txn, posting, new_account):
    """replace the account on a given posting with a new account"""
    # create a new posting with the new account, then remove old and add new
    # from parent transaction
    new_posting = posting._replace(account=new_account)
    txn.postings.remove(posting)
    txn.postings.append(new_posting)


def gain_loss(entries, options_map, config):
    """Insert entries for unmatched transactions in zero-sum accounts.

    Args:
      entries: a list of entry instances

      options_map: a dict of options parsed from the file (not used)

      config: A configuration string, which is intended to be a Python dict
      listing rewrites. Eg:

      {
        "Income.*:Capital-Gains.*" : [":Capital-Gains",  ":Capital-Gains:Gains",  ":Capital-Gains:Losses"],
      }

      The key is the string to match in a posting account. The value is a tuple of 3 elements: pattern to
      replace, replacement for gains, and replacement for losses.

    Returns:
      A tuple of entries and errors. """

    start_time = time.time()
    rewrite_count = 0
    new_accounts = []
    errors = []

    rewrites = literal_eval(config)  # TODO: error check

    for entry in entries:
        if isinstance(entry, data.Transaction):
            postings = list(entry.postings)
            for posting in postings:
                account = posting.account
                if any(re.match(r, account) for r in rewrites):
                    for r in rewrites:
                        if posting.units.number < 0:
                            account = account.replace(rewrites[r][0], rewrites[r][1])  # gains
                        else:
                            account = account.replace(rewrites[r][0], rewrites[r][2])  # losses
                        rewrite_count += 1
                        if account not in new_accounts:
                            new_accounts.append(account)
                    account_replace(entry, posting, account)

    new_open_entries = common.create_open_directives(new_accounts, entries, meta_desc="gains_losses")
    if DEBUG:
        elapsed_time = time.time() - start_time
        print("Gain/loss gains classifier [{:.1f}s]: {} postings classified.".format(elapsed_time, rewrite_count))
    return(new_open_entries + entries, errors)
