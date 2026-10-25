"""Rebooks capital gains accounts into separate short-term and long-term accounts based on length held
according to IRS, US.

Invoke it in your beancount source this way:
    <match_regexp> : [<substring_to_replace>, <replacement_for_short-term>, <replacement_for_long-term>]

  where <match_regexp> is a regexp to match in a posting account.
  Note that <match_regexp> is a regexp while the remaining values are strings

Example:
plugin "long_short" "{
    'Income.*:Taxable:Capital-Gains:' : [':Capital-Gains', ':Capital-Gains:Short', ':Capital-Gains:Long']
    }"

Currently, only a single match_regexp in the dictionary is supported. Additional keys will be ignored.

TODO:
    - support multiple pattern/replacement/replacement sets. Via regexp or via lists

"""

import re
import time
from ast import literal_eval

from beancount.core import data
from dateutil import relativedelta

from beancount_reds_plugins.common import common

DEBUG = 0
__plugins__ = ("long_short",)


def long_short(entries, options_map, config):  # noqa: C901
    """Replace :Capital-Gains: in transactions with :Capital-Gains:Short: and/or :Capital-Gains:Long:"""

    start_time = time.time()
    rewrite_count_matches = rewrite_count_short = rewrite_count_long = 0
    new_accounts = set()
    errors = []

    config_obj = literal_eval(config)
    acct_match_regex = next(iter(config_obj))
    acct_match = re.compile(acct_match_regex)
    account_to_replace, short_account_repl, long_account_repl = config_obj[
        acct_match_regex
    ]

    def contains_shortlong_postings(entry):
        return any(
            short_account_repl in posting.account
            or long_account_repl in posting.account
            for posting in entry.postings
        )

    def contains_generic(entry):
        return any(acct_match.match(posting.account) for posting in entry.postings)

    def is_interesting_entry(entry):
        return contains_generic(entry) and not contains_shortlong_postings(entry)

    def reductions(entry):
        # If the entry doesn't contain a price (p.price == None), it will remain in the parent
        # (:Capital-Gains) account, which can make it a pain to debug. At least warn the user
        # somehow, or collect these in a separate error account
        return [
            p
            for p in entry.postings
            if (p.cost and p.units.number and p.price is not None)
        ]

    def missing_basis(p):
        # Classification needs a cost number (the gain's basis) always, and
        # a cost date (the holding period's start) only when the posting
        # sells a long lot. A cover needs no date: closing a written option
        # or any short position is short-term whatever its holding period
        # (see sale_type).
        return p.cost.number is None or (p.units.number < 0 and p.cost.date is None)

    def sale_type(p, entry_date):
        # The income posting's amount, sign and all: a gain credits
        # (negative), a loss debits (positive).
        gain = (p.price.number - p.cost.number) * p.units.number
        if p.units.number > 0:
            # Closing a written option or any short position is short-term
            # whatever its holding period (US IRC 1234(b); 1233(a) for short
            # sales). The units sign is that fact at entry level: a
            # reduction posting with positive units closes a short.
            return False, gain
        diff = relativedelta.relativedelta(entry_date, p.cost.date)
        # relativedelta is used to account for leap years. IRS' definition is at the bottom of the file
        return diff.years > 1 or (
            diff.years == 1 and (diff.months >= 1 or diff.days >= 1)
        ), gain

    for entry in entries:
        # identify reduction transactions
        # determine long vs short for each lot
        # replace cap gains account with above

        if isinstance(entry, data.Transaction) and is_interesting_entry(entry):
            rewrite_count_matches += 1
            reduction_postings = reductions(entry)
            # Leave the entry unchanged if any reduction lacks what
            # classification needs of it (missing_basis): rebooking only
            # some of its gains would unbalance the user's ledger.
            if any(missing_basis(p) for p in reduction_postings):
                continue
            sale_types = [sale_type(p, entry.date) for p in reduction_postings]
            if not sale_types:
                continue
            short_gains = sum(s[1] for s in sale_types if s[0] is False)
            long_gains = sum(s[1] for s in sale_types) - short_gains

            # record and remove generic capital gains postings
            orig_gains_postings = [
                p for p in entry.postings if acct_match.match(p.account)
            ]
            orig_sum = sum(p.units.number for p in orig_gains_postings)
            for p in orig_gains_postings:
                entry.postings.remove(p)

            # ensure our replacement postings sum up to the original capital gains postings we removed
            diff = orig_sum - (short_gains + long_gains)
            # divide this diff among short/long. TODO: warn if this is over tolerance threshold, because it
            # means that the transaction is probably not accounted for correctly.
            # When the recomputed gains already match, the division below
            # would only pollute their scale (a zero diff still goes
            # through it), so skip it.
            if diff and abs(diff) >= entry.meta["__tolerances__"][p.units.currency]:
                total = short_gains + long_gains
                short_gains += (short_gains / total) * diff
                long_gains += (long_gains / total) * diff

            orig_p = orig_gains_postings[0]

            def add_posting(gains, account_repl):
                new_units = orig_p.units._replace(number=gains)
                new_account = orig_p.account.replace(account_to_replace, account_repl)
                new_accounts.add(new_account)
                new_posting = orig_p._replace(account=new_account, units=new_units)
                entry.postings.append(new_posting)

            # create and add upto two new postings
            if short_gains:
                add_posting(short_gains, short_account_repl)
                rewrite_count_short += 1

            if long_gains:
                add_posting(long_gains, long_account_repl)
                rewrite_count_long += 1

    # create open entries
    new_open_entries = common.create_open_directives(
        new_accounts, entries, meta_desc="<long_short>"
    )
    if DEBUG:
        elapsed_time = time.time() - start_time
        print(
            "Long/short gains classifier [{:.2f}s]: {} matched. {} short, {} long postings added.".format(
                elapsed_time,
                rewrite_count_matches,
                rewrite_count_short,
                rewrite_count_long,
            )
        )
    return new_open_entries + entries, errors


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
#
# Written options and short sales.
#
# IRC 1234(b): gain on closing a written option is short-term however long the option was held.
# IRC 1233(a): rules for gains from short sales.
#
# Both close a short position, which the units sign shows on the reduction posting: positive
# units close a short and are always short-term; negative units sell a long lot and follow
# the one-year rule above.
