# Capital gains classifier plugins for Beancount

Closing out a commodity position results in gains or losses, which could further be (in
the US) short-term or long-term, for tax purposes. There are two plugins included here
that classify and rebook capital gains. See the respective `.py` files for how to
configure them.

## 1. long_short:
_For US based investors._

Rebooks capital gains income into short term or long term accounts based on how long
they have been held. Here is an example to illustrate. The plugin converts:

```
plugin "long_short" "{
   'Income.*Capital-Gains': [':Capital-Gains', ':Capital-Gains:Short', ':Capital-Gains:Long']
   }"
        
2014-01-01 open Assets:Brokerage
2014-01-01 open Assets:Bank
2014-01-01 open Income:Capital-Gains

2014-02-01 * "Buy"
  Assets:Brokerage    100 ORNG {1 USD}
  Assets:Bank        -100 USD

2016-02-01 * "Buy"
  Assets:Brokerage    100 ORNG {2 USD}
  Assets:Bank        -200 USD

2016-03-01 * "Sell"
  Assets:Brokerage   -100 ORNG {1 USD} @ 2.50 USD
  Assets:Brokerage   -100 ORNG {2 USD} @ 2.50 USD
  Assets:Bank         500 USD
  Income:Capital-Gains
```

to:
```
2014-01-01 open Assets:Brokerage
2014-01-01 open Assets:Bank
2014-01-01 open Income:Capital-Gains
2014-01-01 open Income:Capital-Gains:Short
2014-01-01 open Income:Capital-Gains:Long

2014-02-01 * "Buy"
  Assets:Brokerage    100 ORNG {1 USD}
  Assets:Bank        -100 USD

2016-02-01 * "Buy"
  Assets:Brokerage    100 ORNG {2 USD}
  Assets:Bank        -200 USD

2016-03-01 * "Sell"
  Assets:Brokerage   -100 ORNG {1 USD} @ 2.50 USD
  Assets:Brokerage   -100 ORNG {2 USD} @ 2.50 USD
  Assets:Bank         500 USD
  Income:Capital-Gains:Short -50 USD
  Income:Capital-Gains:Long -150 USD
```

As a reference point for performance, the plugin takes 0.03sec to run to modify around
200 transactions across 20k total transactions on a modern laptop.

#### Config:

The plugin config format is:
```
<match_regexp> : [<substring_to_replace>, <replacement_for_short-term>, <replacement_for_long-term>]
```
where `<match_regexp>` is a regexp to match in a posting account. Here is an example:

```
'Income.*:Taxable:Capital-Gains:': [':Capital-Gains', ':Capital-Gains:Short', ':Capital-Gains:Long']
```
   
#### Notes:

- transactions that will be modified:
  - transactions that contain at least one posting with an account string that matches
    `<match_regexp>`
    - such transactions are assumed to contain a lot reduction posting. The lot
      reduction is typically a sale of a (long position) commodity, meaning it involves
      negative number for its units. However, the plugin also woks for closing short
      positions, where a lot reduction posting involves a [positive number](https://beancount.github.io/docs/how_inventories_work.html#homogeneous-and-mixed-inventories)
      of units
  - exception: transactions containing any posting with an account string that contains
    what is specified by `<replacement_for_short-term>` or `<replacement_for_long-term>`
    will be left untouched

- modifications:
  - all postings matching account pattern specified by `<match_regexp>` will be
    removed from matching transactions
  - the sum of the postings inserted will be equal to the sum of existing postings that
    fit the account pattern specified by `<match_regexp>`. Note that if the
    `price - cost` turns out to be different from the `Income` postings specified in
    `<match_regexp>`, the new postings will be scaled to match the latter

- definition of long vs short:
  - implements [IRS' definition](https://www.irs.gov/publications/p550#en_US_publink100010540)
    of "long term" as "more than 1 year" (which could be >= 366 or 367 days depending on
    whether a leap year is involved)

- price must be defined in the lot reduction (sale) transaction


## 2. gain_loss

Rebooks capital gains income into losses and gains based on the posting amount being
positive or negative. Here is an example to illustrate. The plugin converts:

```
plugin "gain_loss" "{
  'Income.*:Capital-Gains.*' : [':Capital-Gains',  ':Capital-Gains:Gains',  ':Capital-Gains:Losses'],
}"

2014-01-01 open Assets:Brokerage
2014-01-01 open Assets:Bank
2014-01-01 open Income:Capital-Gains

2014-02-01 * "Buy"
 Assets:Brokerage    200 ORNG {1 USD}
 Assets:Bank        -200 USD

2016-03-01 * "Sell"
 Assets:Brokerage   -100 ORNG {1 USD} @ 1.50 USD
 Assets:Bank         150 USD
 Income:Capital-Gains

2016-03-02 * "Sell"
 Assets:Brokerage   -100 ORNG {1 USD} @ 0.50 USD
 Assets:Bank          50 USD
 Income:Capital-Gains
```

to:

```
plugin "gain_loss" "{
  'Income.*:Capital-Gains.*' : [':Capital-Gains',  ':Capital-Gains:Gains',  ':Capital-Gains:Losses'],
}"

2014-01-01 open Assets:Brokerage
2014-01-01 open Assets:Bank
2014-01-01 open Income:Capital-Gains

2014-02-01 * "Buy"
 Assets:Brokerage    200 ORNG {1 USD}
 Assets:Bank        -200 USD

2016-03-01 * "Sell"
 Assets:Brokerage   -100 ORNG {1 USD} @ 1.50 USD
 Assets:Bank         150 USD
 Income:Capital-Gains:Gains

2016-03-02 * "Sell"
 Assets:Brokerage   -100 ORNG {1 USD} @ 0.50 USD
 Assets:Bank          50 USD
 Income:Capital-Gains:Losses
```

## Notes
Here is an example of how to invoke both plugins:

```
plugin "beancount_reds_plugins.capital_gains_classifier.long_short" "{
  'Income.*:Taxable:Capital-Gains': [':Capital-Gains', ':Capital-Gains:Short', ':Capital-Gains:Long']
}"

plugin "beancount_reds_plugins.capital_gains_classifier.gain_loss" "{
 'Income.*:Taxable:Capital-Gains:Long.*':  [':Long',  ':Long:Gains',  ':Long:Losses'],
 'Income.*:Taxable:Capital-Gains:Short.*': [':Short', ':Short:Gains', ':Short:Losses'],
 }"
```
