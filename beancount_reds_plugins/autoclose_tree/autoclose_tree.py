"""Closes an account subtree. See accompanying README.md"""

import time
from beancount.core import data
from beancount.core.data import Open, Close

DEBUG = 0
__plugins__ = ('autoclose_tree',)


def autoclose_tree(entries, options_map, config):
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
            subaccounts = [a for a in opens if entry.account in a and a not in closes]
            for s in subaccounts:
                meta = data.new_metadata('<beancount_reds_plugins_close_account_tree>', 0)
                close_entry = data.Close(meta, entry.date, s)
                new_entries.append(close_entry)
                closes.append(s)
                close_count += 1

    if DEBUG:
        elapsed_time = time.time() - start_time
        print("Close account tree [{:.2f}s]: {} close entries added.".format(elapsed_time, close_count))
    return entries + new_entries, errors
