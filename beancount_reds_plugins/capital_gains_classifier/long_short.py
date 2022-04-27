"""Classifies Capital Gains accounts into Short and Long based on length held according to IRS, US.

Invoke it in your beancount source this way:
plugin "long_short" "{
   'generic_account_pat': ':Taxable:Capital-Gains:',
   'short_account_rep':   ':Taxable:Capital-Gains:Short:',
   'long_account_rep':    ':Taxable:Capital-Gains:Long:',
   }"

TODO:
    - support multiple pattern/replacement/replacement sets. Via regexp or via lists

"""

import time

from beancount.core import data
from ast import literal_eval
from dateutil import relativedelta
from beancount_reds_plugins.common import common

DEBUG = 1

__plugins__ = ('long_short',)


def pretty_print_transaction(t):
    print(t.date)
    for p in t.postings:
        print("            ", p.account, p.position)
    print("")


def long_short(entries, options_map, config):
    """Replace :Capital-Gains: in transactions with :Capital-Gains:Short: and/or :Capital-Gains:Long:
    """

    start_time = time.time()
    rewrite_count_short = rewrite_count_long = 0
    new_accounts = set()
    errors = []

    config_obj = literal_eval(config)
    generic_account_pat = config_obj.pop('generic_account_pat', {})
    # Turn into regex
    short_account_rep = config_obj.pop('short_account_rep', {})
    long_account_rep = config_obj.pop('long_account_rep', {})

    def isreduction(entry):
        return any(posting.cost and posting.units.number < 0 for posting in entry.postings)

    def contains_shortlong_postings(entry):
        return any(short_account_rep in posting.account or long_account_rep in posting.account for posting in entry.postings)

    def contains_generic(entry):
        return any(generic_account_pat in posting.account for posting in entry.postings)

    def is_interesting_entry(entry):
        return isreduction(entry) and contains_generic(entry) and not contains_shortlong_postings(entry)

    def reductions(entry):
        return [posting for posting in entry.postings if (posting.cost and posting.units.number < 0)]

    def sale_type(p, entry_date):
        diff = relativedelta.relativedelta(entry_date, p.cost.date)
        gain = (p.cost.number - p.price.number) * abs(p.units.number) # Income is negative
        # relativedelta is used to account for leap years. IRS' definition is at the bottom of the file
        return diff.years > 1 or (diff.years == 1 and (diff.months >= 1 or diff.days >=1)), gain


    for entry in entries:

        # identify reduction transactions
        # determine long vs short for each lot
        # replace cap gains account with above

        if isinstance(entry, data.Transaction) and is_interesting_entry(entry):
            sale_types = [sale_type(p, entry.date) for p in reductions(entry)]
            short_gains = sum(s[1] for s in sale_types if s[0] is False)
            long_gains = sum(s[1] for s in sale_types) - short_gains

            # remove generic gains postings
            orig_gains_postings = [p for p in entry.postings if generic_account_pat in p.account]
            orig_p = orig_gains_postings[0]
            orig_sum = sum(p.units.number for p in orig_gains_postings)
            # TODO: not clear if there are unsafe cases that the code below will do incorrect thing for
            diff = orig_sum - (short_gains + long_gains)
            # divide this diff among short/long. these are typically for expense transactions
            if diff:
                total = short_gains + long_gains
                short_gains += (short_gains/total) * diff
                long_gains += (long_gains/total) * diff

            for p in orig_gains_postings:
                entry.postings.remove(p)

            def add_posting(gains, account_rep):
                new_units = orig_p.units._replace(number=gains)
                new_account = orig_p.account.replace(generic_account_pat, account_rep)
                new_accounts.add(new_account)
                new_posting = orig_p._replace(account=new_account, units=new_units)
                entry.postings.append(new_posting)

            # create and add upto two new postings
            if short_gains:
                add_posting(short_gains, short_account_rep)
                rewrite_count_short += 1

            if long_gains:
                add_posting(long_gains, long_account_rep)
                rewrite_count_long += 1

    # create open entries
    new_open_entries = common.create_open_directives(new_accounts, entries, meta_desc='<long_short>')
    if DEBUG:
        elapsed_time = time.time() - start_time
        print("Long/short gains classifier [{:.2f}s]: {} short, {} long postings added.".format(elapsed_time,
            rewrite_count_short, rewrite_count_long))
    return(new_open_entries + entries, errors)

# IRS references:
#
# https://www.irs.gov/publications/p550#en_US_publink100010540
#
# Long-term or short-term. If you hold investment property more than 1 year, any capital gain or loss is a
# long-term capital gain or loss. If you hold the property 1 year or less, any capital gain or loss is a
# short-term capital gain or loss.
#
# To determine how long you held the investment property, begin counting on the date after the day you
# acquired the property. The day you disposed of the property is part of your holding period.
#
# Example.
#
# If you bought investment property on February 5, 2008, and sold it on February 5, 2009, your holding period
# is not more than 1 year and you have a short-term capital gain or loss. If you sold it on February 6, 2009,
# your holding period is more than 1 year and you have a long-term capital gain or loss.
