"""Opens a set of accounts based on rules. See accompanying README.md"""

import time
from beancount.core import data
from beancount.core.data import Open
# from beancount.parser import printer

DEBUG = 0
__plugins__ = ('autoopen',)


def rules_cash_and_fees(acct, currency, op_currency):
    """TODO: this is hardcoded currently. Make it configurable."""
    s = acct.split(':')
    # root = s[1]
    taxability = s[2]
    leaf = ':'.join(s[3:])
    accts = {
            'cash'    : (f'{acct}:{currency}', [currency], None),      # noqa: E203
            'fees'    : (f'Expenses:Fees-and-Charges:Brokerage-Fees:{taxability}:{leaf}', [currency], None),  # noqa: E203
        }
    return accts


def rules_commodity_leaves_default_booking(acct, ticker, op_currency):
    """TODO: this is hardcoded currently. Make it configurable."""

    return rules_commodity_leaves(acct, ticker, op_currency, include_asset_acct=True)


def rules_commodity_leaves(acct, ticker, op_currency, include_asset_acct=False):
    """TODO: this is hardcoded currently. Make it configurable."""
    s = acct.split(':')
    root = s[1]
    taxability = s[2]
    leaf = ':'.join(s[3:])
    accts = {
        'dividends'    : (f'Income:{root}:{taxability}:Dividends:{leaf}:{ticker}', [op_currency], None),      # noqa: E203
        'interest'     : (f'Income:{root}:{taxability}:Interest:{leaf}:{ticker}',  [op_currency], None),      # noqa: E203
        'cg'           : (f'Income:{root}:{taxability}:Capital-Gains:{leaf}:{ticker}', [op_currency], None),  # noqa: E203
    }
    # bookings cannot be specified via this plugin because bookings run before plugins
    if include_asset_acct:
        accts['main_account'] = (f'{acct}:{ticker}', [ticker], None)

    return accts


def rules_commodity_leaves_cgdists(acct, ticker, op_currency):
    """TODO: this is hardcoded currently. Make it configurable."""
    s = acct.split(':')
    root = s[1]
    taxability = s[2]
    leaf = ':'.join(s[3:])
    accts = {
        'capgainsd_lt' : (f'Income:{root}:{taxability}:Capital-Gains-Distributions:Long:{leaf}:{ticker}', [op_currency], None),   # noqa
        'capgainsd_st' : (f'Income:{root}:{taxability}:Capital-Gains-Distributions:Short:{leaf}:{ticker}', [op_currency], None),  # noqa
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
    # TODO: need to make this specifiable by the metadata param
    op_currency = options_map.get('operating_currency', ['USD'])[0]

    for entry in opens:
        for m in entry.meta:
            if 'autoopen_' in m:
                ruleset = m[9:]
                # Insert open entries
                for leaf in entry.meta[m].split(","):
                    rulesfn = globals()['rules_' + ruleset]
                    for acc_params in rulesfn(entry.account, leaf, op_currency).values():
                        meta = data.new_metadata(entry.meta["filename"], entry.meta["lineno"])
                        new_entries.append(data.Open(meta, entry.date, *acc_params))
                        # printer.print_entry(data.Open(meta, entry.date, *acc_params))

    retval = entries + new_entries

    if DEBUG:
        elapsed_time = time.time() - start_time
        print("Close account tree [{:.2f}s]: {} close entries added.".format(elapsed_time, close_count))

    return retval, errors
