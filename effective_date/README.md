Effective dates plugin for Beancount
------------------------------------

Double entry bookkeeping requires each transaction to occur instantaneously in time. In
Beancount, that translates to each transaction occuring on a single date. However, it is
occasionally useful to view different legs of a transaction occuring across difference
periods of time. For example, consider:

````
2014-12-15 * "Annual Insurance payment for 2015"
    Liabilities:Credit-Card   100 USD
    Expenses:Insurance
````

Here, the payment was made in Dec 2014 for an expense to be booked to 2015. To reflect
this, one could book it thus:

````
2014-12-15 * "Annual Insurance payment for 2015"
    Liabilities:Credit-Card   100 USD
    Assets:Hold:Insurance

2015-01-01 * "Annual Insurance payment for 2015"
    Assets:Hold:Insurance  -100 USD
    Expenses:Insurance
````

The expense is booked in 2015, while the credit card transaction, in 2014. The
"Assets:Hold:Insurance" holds the money for the period in between.

This plugin automates the process above. One can simply enter a single transaction with
an 'effective_date' metadata field for the posting (not the transaction) that needs to
occur later (or earlier):

````
2014-12-15 * "Annual Insurance payment for 2015"
    Liabilities:Credit-Card   100 USD
    Expenses:Insurance
      effective_date: 2015-01-01
````

The plugin also allows for legs to occur on multiple different dates. For example:

````
2015-02-01 * "Car insurance: 3 months"
 Liabilities:Mastercard    -600 USD
 Expenses:Car:Insurance     200 USD
   effective_date: 2015-03-01
 Expenses:Car:Insurance     200 USD
   effective_date: 2015-04-01
 Expenses:Car:Insurance     200 USD
   effective_date: 2015-05-01
````

The examples.bc shows you how the plugin can be configured for your choice of holding
accounts.
