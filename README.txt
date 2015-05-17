Description:
------------
Plugin for accounts that should sum up to zero. Determines transactions
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

I've found the zerosum to be very useful in several scenarios. For example:

- reimbursements: I book these to a reimbursement account at the time of purchase, and
  at the time the reimbursement arrives. Assets:Reimbursement:Workplace account tracks
  reimbursements. When the zerosum plugin is used, it moves all matches to a different
  account, and so, only the outstanding reimbursements (the ones not yet paid) are left
  behind in Assets:Reimbursements:Workplace

- mail in rebates: the Assets:Rebates account tracks all mail-in rebates. When the
  zerosum plugin is used, it moves all matches to a different account, and so, only the
  outstanding rebates are in Assets:Rebates

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

Example:
--------
We use the included zerosum-example.beancount (reproduced below) as the minimum
beancount file for this example. The plugin configuration directives is at the top of
this file, and the output of bean-query is included for illustration.

plugin "beancount.plugins.zerosum" "{
 'zerosum_accounts' : { 
    'Assets:Reimbursements:Workplace' : ('Assets:Reimbursements-Received:Workplace',   40),
    'Assets:Rebates'                  : ('Assets:Zerosum-Matched:Rebates',            180),
  }
 }"


2000-01-01 open Liabilities:Credit-Card         USD
2000-01-01 open Assets:Reimbursements:Workplace USD
2000-01-01 open Assets:Bank:Checking            USD
2000-01-01 open Expenses:Electronics            USD
2000-01-01 open Assets:Rebates                  USD

2010-01-01 * "Office Store" "Pens and pencils"
     Liabilities:Credit-Card            -25 USD
     Assets:Reimbursements:Workplace

2010-01-01 * "Office Store" "Writing pad"
     Liabilities:Credit-Card            -7 USD
     Assets:Reimbursements:Workplace

2010-02-03 * "Reimbursement"
     Assets:Bank:Checking                25 USD
     Assets:Reimbursements:Workplace 

2010-01-01 * "Smartphone"
     Liabilities:Credit-Card           -250 USD
     Assets:Rebates                     100 USD
     Expenses:Electronics

2010-05-04 * "Rebate check"
     Assets:Bank:Checking               100 USD
     Assets:Rebates

2010-01-01 * "Camera"
     Liabilities:Credit-Card           -300 USD
     Assets:Rebates                      50 USD
     Expenses:Electronics


bean-query output:

$ bean-query zerosum-example.beancount
Zerosum: 2/4 postings matched. 0 multiple matches. 2 new accounts added.
Input file: "Beancount"
Ready with 13 directives (14 postings in 6 transactions).

beancount> balances
                account                  sum_posi
---------------------------------------- --------
Assets:Bank:Checking                      125 USD
Assets:Rebates                             50 USD
Assets:Reimbursements-Received:Workplace
Assets:Reimbursements:Workplace             7 USD
Assets:Zerosum-Matched:Rebates
Liabilities:Credit-Card                  -582 USD
Expenses:Electronics                      400 USD
beancount>


As you can see, the received reimbursement got moved into the specified target
account (Assets:Reimbursements-Received:Workplace), while the one not received
(for $7) remains in its original account. Same for the rebate. Target accounts
always sum up to zero.


References:
[1] Beancount: https://bitbucket.org/blais/beancount/, http://furius.ca/beancount/
[2] https://groups.google.com/d/msg/beancount/z9sPboW4U3c/UfJbIVzwmpMJ
[3] https://groups.google.com/forum/#!topic/beancount/MU6KozsmqGQ

