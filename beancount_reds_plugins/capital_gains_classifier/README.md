# Capital gains classifier plugins for Beancount


There are two plugins included here. See the respective `.py` files for info on how to
configure them.

## 1. long_short:
_For US based investors._

Rebooks capital gains income into short term or long term accounts based on how long
they have been held. Here is an example to illustrate. The plugin converts:

```
plugin "long_short" "{
   'generic_account_pat': ':Capital-Gains',
   'short_account_rep':   ':Capital-Gains:Short',
   'long_account_rep':    ':Capital-Gains:Long',
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

As a reference point for performance, the plugin takes 0.02sec to run to modify around
200 transactions across 20k total transactions on a modern laptop.
   
#### Finer points:
- transactions that will be modified:
  - only modifies transactions that contain at least one posting with an account string
    that contains the value specified by `generic_account_pat`
  - exception: transactions containing any posting with an account string that contains
    what is specified by `short_account_rep` or `long_account_rep` will be left
    untouched

- modifications:
  - all postings matching account pattern specified by `generic_account_pat` will be
    removed from matching transactions
  - the sum of the postings inserted will be equal to the sum of existing postings that
    fit the account pattern specified by `generic_account_pat`

- definition of long vs short:
  - implements [IRS' definition](https://www.irs.gov/publications/p550#en_US_publink100010540)
    of "long term" as "more than 1 year" (which could be >= 366 or 367 days depending on
    whether a leap year is involved

- price must be defined in the lot reduction (sale) transaction


## 2. gain_loss (Warning: under development)

Rebooks capital gains income into losses and gains.

For example, the plugin rebooks transactions from an account like:
```
Income:Capital-Gains:GTrade
```

into:

```
Income:Capital-Gains:Losses:GTrade
Income:Capital-Gains:Gains:GTrade
```

based on whether the posting into that account is positive or negative.

