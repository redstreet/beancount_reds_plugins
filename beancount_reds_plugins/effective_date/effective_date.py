"""Beancount plugin to implement per-posting effective dates. See README.md for more."""

from ast import literal_eval
import copy
import datetime
import random
import string
import sys
import time
from beancount.core import data
from beancount_reds_plugins.common import common
from beancount_reds_plugins.effective_date.legacy_effective_date_transaction \
    import effective_date_transaction

DEBUG = 0

__plugins__ = ['effective_date']
# to enable the older transaction-level hacky plugin, now renamed to effective_date_transaction
# __plugins__ = ['effective_date', 'effective_date_transaction']

LINK_FORMAT = 'edate-{date}-{random}'


def has_valid_effective_date(posting):
    return posting.meta is not None and \
             'effective_date' in posting.meta and \
             type(posting.meta['effective_date']) is datetime.date


def has_posting_with_valid_effective_date(entry):
    for posting in entry.postings:
        if has_valid_effective_date(posting):
            return True
    return False


def create_new_effective_date_entry(entry, date, hold_posting, original_posting):
    def cleaned(p):
        clean_meta = copy.deepcopy(p.meta)
        clean_meta.pop('effective_date', None)
        return p._replace(meta=clean_meta)

    new_meta = {'original_date': entry.date}
    effective_date_entry = entry._replace(date=date, meta={**entry.meta, **new_meta},
                                          postings=[cleaned(hold_posting), cleaned(original_posting)])
    return effective_date_entry


def build_config(config):
    holding_accts = {}
    if config:
        holding_accts = literal_eval(config)
    if not holding_accts:
        if DEBUG:
            print("effective_date: Using default config", file=sys.stderr)
        holding_accts = {
                'Expenses': {'earlier': 'Liabilities:Hold:Expenses', 'later': 'Assets:Hold:Expenses'},
                'Income':   {'earlier': 'Assets:Hold:Income', 'later': 'Liabilities:Hold:Income'},
                }
    return holding_accts


def effective_date(entries, options_map, config):
    """Effective dates

    Args:
      entries: a list of entry instances
      options_map: a dict of options parsed from the file
      config: A configuration string, which is intended to be a Python dict
        mapping match-accounts to a pair of (negative-account, position-account)
        account names.
    Returns:
      A tuple of entries and errors.

    """
    start_time = time.time()
    errors = []
    holding_accts = build_config(config)

    interesting_entries = []
    filtered_entries = []
    new_accounts = set()
    for entry in entries:
        if isinstance(entry, data.Transaction) and has_posting_with_valid_effective_date(entry):
            interesting_entries.append(entry)
        else:
            filtered_entries.append(entry)

    # if DEBUG:
    #     print("effective_date: ------")
    #     for e in interesting_entries:
    #         printer.print_entry(e)
    #     print("effective_date: ------")

    # add a link to each effective date entry. this gets copied over to the newly created effective date
    # entries, and thus links each set of effective date entries
    interesting_entries_linked = []
    for entry in interesting_entries:
        rand_string = ''.join(random.choice(string.ascii_lowercase) for i in range(3))
        date = str(entry.date).replace('-', '')[2:]
        link = LINK_FORMAT.format(date=str(date), random=rand_string)
        new_entry = entry._replace(links=(entry.links or set()) | set([link]))
        interesting_entries_linked.append(new_entry)

    new_entries = []
    for entry in interesting_entries_linked:
        modified_entry_postings = []
        for posting in entry.postings:
            if not has_valid_effective_date(posting):
                modified_entry_postings += [posting]
            else:
                found_acct = ''
                for acct in holding_accts:
                    if posting.account.startswith(acct):
                        found_acct = acct

                # find earlier or later (is this necessary?)
                holding_account = holding_accts[found_acct]['earlier']
                if posting.meta['effective_date'] > entry.date:
                    holding_account = holding_accts[found_acct]['later']

                # Replace posting in original entry with holding account
                new_posting = posting._replace(account=posting.account.replace(found_acct, holding_account))
                new_accounts.add(new_posting.account)
                modified_entry_postings.append(new_posting)

                # Create new entry at effective_date
                hold_posting = new_posting._replace(units=-posting.units)
                new_entry = create_new_effective_date_entry(entry, posting.meta['effective_date'],
                                                            hold_posting, posting)
                new_entries.append(new_entry)
        modified_entry = entry._replace(postings=modified_entry_postings)
        new_entries.append(modified_entry)

    # if DEBUG:
    #     print("Output results:")
    #     for e in new_entries:
    #         printer.print_entry(e)

    if DEBUG:
        elapsed_time = time.time() - start_time
        print("effective_date [{:.1f}s]: {} entries inserted.".format(elapsed_time, len(new_entries)))

    new_open_entries = common.create_open_directives(new_accounts, entries, meta_desc='<effective_date>')
    retval = new_open_entries + new_entries + filtered_entries
    return retval, errors


# TODO
# -----------------------------------------------------------------------------------------------------------
# Bug:
# below will fail because expense account was opened too late in the source:
# 2014-01-01 open Expenses:Taxes:Federal
#
# 2014-02-01 * "Estimated taxes for 2013"
# Liabilities:Mastercard    -2000 USD
# Expenses:Taxes:Federal  2000 USD
#   effective_date: 2013-12-31
