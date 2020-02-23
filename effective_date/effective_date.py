"""Plugin to implement effective dates. Originally intended for tax purpuses,
but can now be used for any generalized case."""


import collections

from beancount.core.amount import ZERO
from beancount.core import data
from beancount.core import account
from beancount.core import getters
from beancount.core import flags
from beancount.ops import holdings
from beancount.parser import options
from beancount.parser import printer
import datetime
import time
import string
import random

DEBUG = 0

__plugins__ = ['effective_date']


# TODO:
# - open newly needed accounts automatically

# - when a posting to an "Expense:" account has a date that is prior to the
# transaction date, the amount outstanding between the two dates likely needs
# to be a booked to a Liabilities:Hold account (same as the example above)

# - when a posting to an "Expense:" account has a date that occurrs after the
# transaction date, the amount outstanding between the two dates likely needs
# to be booked to an Assets:Hold account.


LINK_FORMAT = 'effective-date-link-{}'


def effective_date(entries, options_map, config):
    """Effective dates

    Changes this:

    ------(
    2014-02-01 "Estimated taxes for 2013"
      effective_date: 2013-12-31
      Liabilities:Mastercard    -2000 USD
      Expenses:Taxes:Federal  2000 USD
    )------

    into this:
    ------(
    2014-02-01 "Estimated taxes for 2013"
      Liabilities:Mastercard     -2000 USD
      Liabilities:Hold:Taxes:Federal 2000 USD

    2013-12-31 "Estimated taxes for 2013"
      Liabilities:Hold:Taxes:Federal    -2000 USD
      Expenses:Taxes:Federal    2000 USD
    )------


    # Example 2: realizing income earlier (eg: for taxes, accounting, etc.):
    ------(
    2017-01-03 "Paycheck"
      effective_date: 2016-12-31
      Income:Employment    -2000 USD
      Assets:Bank  2000 USD
    )------

    into this:
    ------(
    2016-12-31 "Paycheck"
      Income:Employment    -2000 USD
      Assets:Hold:Income:Employment    2000 USD

    2014-02-01 "Paycheck"
      Assets:Hold:Income:Employment    -2000 USD
      Assets:Bank  2000 USD
    )------


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

    interesting_entries = []
    filtered_entries = []
    new_accounts = []
    for entry in entries:
        outlist = (interesting_entries
                   if (isinstance(entry, data.Transaction) and 
                       'effective_date' in entry.meta and
                       type(entry.meta['effective_date']) == datetime.date)
                   else filtered_entries)
        outlist.append(entry)

    # print("------")
    # for e in interesting_entries:
    #     # print(e)
    #     printer.print_entry(e)
    #     print(type(e.meta.effective_date) == datetime.date)
    #     print("")
    # print("------")

    modcount = 0
    new_entries = []
    for entry in interesting_entries:
        modified_entry_postings = []
        effective_date_entry_postings = []
        found = False
        accts_to_split = {
                'Expenses': {'earlier': 'Liabilities:Hold', 'later': 'Assets:Hold'},
                'Income':   {'earlier': 'Assets:Hold', 'later': 'Liabilities:Hold'},
                }
        for posting in entry.postings:
            if any(acct in posting.account for acct in accts_to_split):
                found_acct = ''
                for acct in accts_to_split:
                    if posting.account.startswith(acct):
                        found_acct = acct
                found = True
                modcount += 1

                holding_account = accts_to_split[found_acct]['earlier']
                if entry.meta['effective_date'] > entry.date:
                    holding_account = accts_to_split[found_acct]['later']
                new_posting = posting._replace(account=posting.account.replace(found_acct, holding_account))
                if new_posting.account not in new_accounts:
                    new_accounts.append(new_posting.account)
                modified_entry_postings += [new_posting]
                effective_date_entry_postings  += [posting]

                effective_date_entry_postings  += [posting._replace(
                    account=posting.account.replace(found_acct, holding_account),
                    units=-posting.units)]

                if posting.account not in new_accounts:
                    new_accounts.append(posting.account)

            else:
                modified_entry_postings += [posting]

        if found:
            rand_string = ''.join(random.choice(string.ascii_uppercase) for i in range(5))
            link = LINK_FORMAT.format(rand_string)
            # modified_entry = data.entry_replace(entry, postings=modified_entry_postings,
            #                                     links=(entry.links or set()) | set([link]))
            modified_entry = entry._replace(postings=modified_entry_postings,
                                                links=(entry.links or set()) | set([link]))

            effective_date_entry_narration = entry.narration + " (originally: {})".format(str(entry.date))
            # effective_date_entry = data.entry_replace(entry, date=entry.meta['effective_date'],
            #         postings=effective_date_entry_postings,
            #         narration = effective_date_entry_narration,
            #         links=(entry.links or set()) | set([link]))
            new_meta = {'original_date': entry.date}
            effective_date_entry = entry._replace(date=entry.meta['effective_date'],
                    meta={**entry.meta, **new_meta},
                    postings=effective_date_entry_postings,
                    narration = effective_date_entry_narration,
                    links=(entry.links or set()) | set([link]))
            new_entries += [modified_entry, effective_date_entry]
        else:
            new_entries += [entry]

    # print("Output results:")
    # for e in new_entries:
    #     printer.print_entry(e)

    if DEBUG:
        elapsed_time = time.time() - start_time
        print("effective_date [{:.1f}s]: {} entries inserted.".format(elapsed_time, modcount))

    new_open_entries = create_open_directives(new_accounts, entries)
    retval = new_open_entries + new_entries + filtered_entries
    return(retval, errors)

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

# TODO
# -----------------------------------------------------------------------------------------------------------
# - handle >=3 posting transactions
# 2010-01-02 * "Income"
#   effective_date: 2016-12-31
#   Assets:Banks   100
#   Income:Source  -110
#   Expenses:Income-Tax 10
