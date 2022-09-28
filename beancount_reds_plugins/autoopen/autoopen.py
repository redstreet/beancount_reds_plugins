"""Opens a set of accounts based on rules. See accompanying README.md"""

import time
from beancount.core import data
from beancount.core.data import Open, Close

DEBUG = 0
__plugins__ = ('autoopen',)

def commodity_leaves(acct, ticker):
    """TODO: this is hardcoded currently. Make it configurable."""
    s = acct.split(':')
    root = s[1]
    taxability = s[2]
    leaf = ':'.join(s[3:])
    accts = {
        'main_account'   : (f'{acct}:{ticker}', ticker, data.Booking.STRICT),
        'dividends'      : (f'Income:{root}:{taxability}:Dividends:{leaf}:{ticker}', 'USD', None),
        'interest'       : (f'Income:{root}:{taxability}:Interest:{leaf}:{ticker}', 'USD', None),
        'cg'             : (f'Income:{root}:{taxability}:Capital-Gains:{leaf}:{ticker}', 'USD', None),
        'capgainsd_lt'   : (f'Income:{root}:{taxability}:Capital-Gains-Distributions:Long:{leaf}:{ticker}', 'USD', None),
        'capgainsd_st'   : (f'Income:{root}:{taxability}:Capital-Gains-Distributions:Short:{leaf}:{ticker}', 'USD', None),
    }
    return accts


def autoopen(entries, options_map):
    """Insert open entries based on rules.

    Args:
      entries: a list of entry instances
      options_map: a dict of options parsed from the file (not used)
    Returns:
      A tuple of entries and errors. """

    start_time = time.time()
    close_count = 0
    new_entries = []
    errors = []

    opens = [e for e in entries if isinstance(e, Open)]

    for entry in opens:
        if 'autoopen_commodity_leaves' in entry.meta:
            # Insert open entries
            for leaf in entry.meta['commodity_leaves'].split(","):
                for acc_params in commodity_leaves(entry.account, leaf).values():
                    meta = data.new_metadata(entry.meta["filename"], entry.meta["lineno"])
                    new_entries.append(data.Open(meta, entry.date, *acc_params))

    retval = entries + new_entries

    if DEBUG:
        elapsed_time = time.time() - start_time
        print("Close account tree [{:.2f}s]: {} close entries added.".format(elapsed_time, close_count))
    return retval, errors
