"""Closes an account subtree. See accompanying README.md"""

import time
from beancount.core import data
from beancount.core.data import Open, Close

DEBUG = 0
__plugins__ = ('autoclose_tree',)


def autoclose_tree(entries, options_map):
    """Insert close entries for all subaccounts of a closed account.

    Args:
      entries: a list of entry instances

      options_map: a dict of options parsed from the file (not used)

      config: A configuration string, which is intended to be a Python dict. Currently, this is
      ignored.

    Returns:
      A tuple of entries and errors. """

    start_time = time.time()
    close_count = 0
    new_entries = []
    errors = []

    opens = [e.account for e in entries if isinstance(e, Open)]
    closes = [e.account for e in entries if isinstance(e, Close)]

    for entry in entries:
        if isinstance(entry,  Close):
            subaccounts = [a for a in opens if entry.account + ':' in a and a not in closes]
            for s in subaccounts:
                meta = data.new_metadata('<beancount_reds_plugins_close_account_tree>', 0)
                close_entry = data.Close(meta, entry.date, s)
                new_entries.append(close_entry)
                closes.append(s)
                close_count += 1
            if entry.account in opens:
                new_entries.append(entry)
        else:
            new_entries.append(entry)

    # beancount.plugins.auto_accounts, if used in conjunction with this plugin, inserts an Open
    # entry for empty parent accounts which we are trying to close. For example:

    # plugin "beancount.plugins.auto_accounts"
    # 2021-06-17 close Expenses:Non-Retirement:Auto:Fit
    # plugin "beancount_reds_plugins.autoclose_tree.autoclose_tree"
    # 2019-01-01 * "Transaction"
    #   Expenses:Non-Retirement:Auto:Fit:Insurance      10 USD
    #   Expenses:Non-Retirement:Auto:Fit:Gas            20 USD
    #   Assets:Transfer

    # Above, auto_accounts inserts an Open for 'Expenses:Non-Retirement:Auto:Fit:Gas' on 2021-06-17
    # since it appears in a close directive. But that's not what we want. The semantic of the close
    # when u used with this plugin is: "close all children, and close the parent if it was opened
    # earlier. Below, we filter out entries to correctly handle this scenario:

    opens = [(e.account, e.date) for e in entries if isinstance(e, Open)]
    closes = [(e.account, e.date) for e in entries if isinstance(e, Close)]
    retval = []
    for entry in new_entries:
        if isinstance(entry, Open) and (entry.account, entry.date) in closes:
            continue
        if isinstance(entry, Close) and (entry.account, entry.date) in opens:
            continue
        retval.append(entry)

    if DEBUG:
        elapsed_time = time.time() - start_time
        print("Close account tree [{:.2f}s]: {} close entries added.".format(elapsed_time, close_count))
    return retval, errors
