Effective dates plugin for Beancount
------------------------------------

An entire Beancount transaction must occur on the same day, but in some instances, one
or more legs must be booked to a different date. For example:

````
2014-12-15 * "Annual Insurance payment for 2015"
    Liabilities:Credit-Card   100 USD
    Expenses:Insurance
````

Here, the payment was made in Dec 2014 for an expense to be booked to 2015. In this
case, one would normally have to do:

````
2014-12-15 * "Annual Insurance payment for 2015"
    Liabilities:Credit-Card   100 USD
    Assets:Hold:Insurance


2015-01-01 * "Annual Insurance payment for 2015"
    Assets:Hold:Insurance  -100 USD
    Expenses:Insurance
````

This plugin automates the process above. One can simply enter a single transaction with
an 'effective_date' metadata field:

````
2014-12-15 * "Annual Insurance payment for 2015"
    effective_date: 2015-01-01
    Liabilities:Credit-Card   100 USD
    Expenses:Insurance
````


The plugin also changes this:


````
    2014-02-01 "Estimated taxes for 2013"
      effective_date: 2013-12-31
      Liabilities:Mastercard    -2000 USD
      Expenses:Taxes:Federal  2000 USD
````


into this:


````
    2014-02-01 "Estimated taxes for 2013"
      Liabilities:Mastercard     -2000 USD
      Liabilities:Hold:Taxes:Federal 2000 USD

    2013-12-31 "Estimated taxes for 2013"
      Liabilities:Hold:Taxes:Federal    -2000 USD
      Expenses:Taxes:Federal    2000 USD
````

Future work:
------------
Currently, this plugin has many limitations. In particular:
- works reliably only for transactions with two legs
- at least one leg must be booked to an Expense account

