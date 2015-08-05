"""Plugin for accounts that should sum up to zero. Determines transactions
that when taken together, sum up to zero, and move them to a specified
account. The remaining entries are the 'unmatched' ones, that need attention
from the user.

Motivation:
-----------

Real-world transfers frequently occur between accounts. For example, between a
checking account and an investment account. When double entry bookkeeping is
used to track such transfers, we end up with two problems:

    a) when account statements are converted to double-entry format, the user
    has to manually match the transfers on account statements from the two
    institutions involved, and remove one of the entries since they are
    redundant.

    b) even when (a) is done, the transfer might take a day or more to
    complete: the two accounts involved would then reflect the transfer on
    different dates.

Since the money is truly missing from all the physical accounts for the period
of transfer, they can be accounted for as shown in this example:

2005-01-01 Transfer
  Assets:Bank_of_Ameriplus  -20 USD
  ZeroSumAccount:Transfers

2005-01-03 Transfer
  Assets:TB_Trading  20 USD
  ZeroSumAccount:Transfers

Doing so has a few advantages:

    a) on 2005-01-02, your assets are accurately represented:
    Bank_of_Ameriplus is short by $20, TB_Trading still doesn't have it, and
    the ZeroSumAccount:Transfers account captures that the money is still
    yours, but is "in flight."

    b) One can convert each bank's transactions directly into double-entry
    ledger statements. No need to remove the transaction from one of the
    banks. When you look at your journal files for each account, they match
    your account statements exactly.

    c) Import/conversion (from say, a bank .csv or .ofx) is easier, because
    your import scripts don't have to figure out where a transfer goes, and
    can simply assign transfers to  ZeroSumAccount:Transfers

    d) If there is a problem, your ZeroSumAccount:Transfers will sum to a
    non-zero value. Errors can therefore be found easily.


What this plugin does:
----------------------

Account statements from institutions can be directly converted to double-entry
format, with transfers simply going to a special transfers account (eg:
Assets:ZeroSumAccount:Transfers).

In this plugin, we identify sets of postings in the specified ZeroSum accounts
that sum up to zero, and move them to a specified target account. This target
account will always sum up to zero and needs no further attention. The
postings remaining in the original ZeroSum accounts were the ones that could
not be matched, and potentially need attention.

The plugin operates on postings (not transactions) in the ZeroSum accounts.
This way, transactions with multiple postings to a ZeroSum account are still
matched without special handling.

The following examples will be matched and moved by this plugin:

    Example 1:
    ----------
    Input:
        2005-01-01 Transfer
          Assets:Bank_of_Ameriplus  -20 USD
          ZeroSumAccount:Transfers

        2005-01-03 Transfer
          Assets:TB_Trading  20 USD
          ZeroSumAccount:Transfers
    Output:
        2005-01-01 Transfer
          Assets:Bank_of_Ameriplus  -20 USD
          ZeroSumAccount-Matched:Transfers

        2005-01-03 Transfer
          Assets:TB_Trading  20 USD
          ZeroSumAccount-Matched:Transfers

    Example 2 (Only input shown):
    -----------------------------
    2005-01-01 Transfer
      Assets:Bank_of_Ameriplus  -20 USD
      ZeroSumAccount:Transfers   10 USD
      ZeroSumAccount:Transfers   10 USD

    2005-01-03 Transfer
      Assets:TB_Trading_A  10 USD
      ZeroSumAccount:Transfers

    2005-01-04 Transfer
      Assets:TB_Trading_B  10 USD
      ZeroSumAccount:Transfers

The following examples will NOT be matched:

    Example A:
    ----------
    2005-01-01 Transfer
      Assets:Bank_of_Ameriplus  -20 USD
      ZeroSumAccount:Transfers   10 USD
      ZeroSumAccount:Transfers   10 USD

    2005-01-03 Transfer
      Assets:TB_Trading  20 USD
      ZeroSumAccount:Transfers

    Example B:
    ----------
    2005-01-01 Transfer
      Assets:Bank_of_Ameriplus  -20 USD
      ZeroSumAccount:Transfers

    2005-01-03 Transfer
      Assets:TB_Trading_A  10 USD
      ZeroSumAccount:Transfers

    2005-01-03 Transfer
      Assets:TB_Trading_B  10 USD
      ZeroSumAccount:Transfers


The plugin does not append/remove the original set of input transaction
entries. It only changes the accounts to which postings are made. The plugin
also automatically adds "Open" directives for the target accounts to which
matched transactions are moved.

Invoking the plugin:
--------------------
First, an example:

    plugin "beancount.plugins.zerosum" "{
     'zerosum_accounts' : { 
     'Assets:Zero-Sum-Accounts:Bank-Account-Transfers' : ('Assets:ZSA-Matched:Bank-Account-Transfers', 30),
     'Assets:Zero-Sum-Accounts:Credit-Card-Payments'   : ('Assets:ZSA-Matched:Credit-Card-Payments'  ,  6),
     'Assets:Zero-Sum-Accounts:Temporary'              : ('Assets:ZSA-Matched:Temporary'             , 90),
      }
     }"

As the example shows, the argument is a dictionary where the keys are the set
of accounts on which the plugin should operate. The values are
(target_account, date_range), where the target_account is the account to which
the plugin should move matched postings, and the date_range is the range over
which to check for matches for that account.

"""

import collections

from beancount.core.amount import ZERO
from beancount.core import data
from beancount.core import account
from beancount.core import getters
from beancount.core import position
from beancount.core import flags
from beancount.ops import holdings
from beancount.ops import prices
from beancount.parser import options
from beancount.parser import printer


__plugins__ = ('zerosum',)

def pretty_print_transaction(t):
    print(t.date)
    for p in t.postings:
        print("            ", p.account, p.position)
    print("")


# replace the account on a given posting with a new account
def account_replace(txn, posting, new_account):
    # create a new posting with the new account, then remove old and add new
    # from parent transaction
    new_posting = posting._replace(account=new_account)
    txn.postings.remove(posting)
    txn.postings.append(new_posting)



ZerosumError = collections.namedtuple('ZerosumError', 'source message entry')

# TODO:
# - if account metadata has 'zerosumaccountcheck' set to true, then check it
# - take plugin params from metadata (including date_range)
# - add 'Matched' accounts to definition list automatically from plugin
# - create a beancount-link between matches for debugging?


def zerosum(entries, options_map, config):
    """Insert entries for unmatched transactions in zero-sum accounts.

    Args:
      entries: a list of entry instances

      options_map: a dict of options parsed from the file (not used)

      config: A configuration string, which is intended to be a Python dict
      mapping zerosum account name -> (matched zerosum account name,
      date_range). See example for more info.

    Returns:
      A tuple of entries and errors.

    """


    config_obj = eval(config, {}, {})
    if not isinstance(config_obj, dict):
        raise RuntimeError("Invalid plugin configuration: should be a single dict.")

    zs_accounts_list = config_obj.pop('zerosum_accounts', {})

    errors = []
    new_accounts = []
    zerosum_postings_count = 0
    match_count = 0
    multiple_match_count = 0
    EPSILON_DELTA = 0.0099
    for zs_account,account_config in zs_accounts_list.items():

        date_range = account_config[1]
        zerosum_txns = []
        non_zerosum_entries = []
        # this loop bins each entry into either zerosum_txns or non_zerosum_entries
        for entry in entries:
            outlist = (zerosum_txns
                       if (isinstance(entry, data.Transaction) and
                           any(posting.account == zs_account for posting in entry.postings))
                       else non_zerosum_entries)
            outlist.append(entry)

        # algorithm: iterate through zerosum_txns (zerosum transactions). For each
        # transaction, for each of its postings involving zs_account, try to
        # find a match across all the other zerosum_txns. If a match is found,
        # replace the account name in the the pair of postings.

        # This would be easier if we could ignore transactions and just
        # iterate across posting. But we cannot do so because postings are
        # tuples, and therefore immutable: we have to replace a posting with a
        # newly created posting in order to make a change to its account when
        # a matching pair is found. If we were iterating across postings, we
        # would be adding/removing from the posting list we are iterating
        # through, which is not a good idea.

        for txn in zerosum_txns:
            for posting in txn.postings:
                if posting.account == zs_account:
                    zerosum_postings_count += 1
                    matches = [(p, t) for t in zerosum_txns for p in t.postings
                            if (p.account == zs_account and
                            abs(p.position.number + posting.position.number) < EPSILON_DELTA and
                            abs((t.date - txn.date).days) <= date_range)
                            ]

                    # replace accounts in the pair
                    if len(matches) >=1:
                        match_count += 1
                        if len(matches) > 1:  #TODO: check if closest date is
                            # picked. zerosum_txns is sorted by date, so the
                            # earliest posting might be picked, which might not
                            # be the same as the closest
                            multiple_match_count += 1

                        account_replace(txn,           posting,       account_config[0])
                        account_replace(matches[0][1], matches[0][0], account_config[0])
                        if account_config[0] not in new_accounts:
                            new_accounts.append(account_config[0])

    # TODO: should ideally track account specific earliest date
    new_open_entries = create_open_directives(new_accounts, entries)

    print("Zerosum: {}/{} postings matched. {} multiple matches. {} new accounts added.".format(match_count, zerosum_postings_count, multiple_match_count, len(new_open_entries)))
    
    # it's important to preserve and return 'entries', which was the input
    # list. This way, we won't inadvertantly add/remove entries from the
    # original list of entries.
    return(new_open_entries + entries, errors)



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
            meta = data.new_metadata(meta.filename, 0)
            open_entry = data.Open(meta, earliest_date, account_, None, None)
            new_open_entries.append(open_entry)
    return(new_open_entries)
