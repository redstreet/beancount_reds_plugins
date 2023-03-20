"""This plugin inserts close directives for all of an account's descendants when an account is
closed. Unopened parent accounts can also be closed. Any explicitly specified close is left
untouched.

For example, given this:

```
2017-11-10 open Assets:Brokerage:AAPL
2017-11-10 open Assets:Brokerage:ORNG
2018-11-10 close Assets:Brokerage  ; this account does not necessarily need to be opened
```

the plugin turns it into:
```
2017-11-10 open Assets:Brokerage:AAPL
2017-11-10 open Assets:Brokerage:ORNG
2018-11-10 close Assets:Brokerage:AAPL
2018-11-10 close Assets:Brokerage:ORNG
```

Invoke this plugin _after_ any plugins that generate `open` directives for account trees that you
want to auto close. An example is the `auto_accounts` plugin that ships with Beancount:

```
plugin "beancount.plugins.auto_accounts"
plugin "beancount.plugins.close_tree"
```
"""

import time
from beancount.core import data
from beancount.core.data import Open, Close

DEBUG = 0
__plugins__ = ('autoclose_tree',)


def autoclose_tree(entries, unused_options_map):
    """Insert close entries for all subaccounts of a closed account.

    Args:
      entries: A list of directives. We're interested only in the Open/Close instances.
      unused_options_map: A parser options dict.
    Returns:
      A tuple of entries and errors. """

    start_time = time.time()
    close_count = 0
    new_entries = []
    errors = []

    opens = set(e.account for e in entries if isinstance(e, Open))
    closes = set(e.account for e in entries if isinstance(e, Close))

    for entry in entries:
        if isinstance(entry,  Close):
            subaccounts = [a for a in opens if a.startswith(entry.account + ':') and a not in closes]
            for subacc in subaccounts:
                meta = data.new_metadata('<beancount.plugins.close_tree>', 0)
                close_entry = data.Close(meta, entry.date, subacc)
                new_entries.append(close_entry)
                closes.add(subacc)  # So we don't attempt to re-close a grandchild that a child closed
            if entry.account in opens:
                new_entries.append(entry)
        else:
            new_entries.append(entry)

    if DEBUG:
        elapsed_time = time.time() - start_time
        print("Close account tree [{:.2f}s]: {} close entries added.".format(elapsed_time, close_count))
    return new_entries, errors
