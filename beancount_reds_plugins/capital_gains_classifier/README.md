# Capital gains classifier plugin for Beancount

## WARNING: These plugins are experimental / under development

There are two plugins included here. See the respective `.py` files for info on how to
configure them:

## 1. long_short:
Classifies sales into short term or long term capital gains based on how long they have
been held, like so:

Converts:
```
plugin "long_short" "{
   'generic_account_pat':   ':Capital-Gains',
   'short_account_rep': ':Capital-Gains:Short',
   'long_account_rep':  ':Capital-Gains:Long',
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

WARNINGS:
- still under development
- doesn't work for leap years yet
- doesn't distinguish between reductions and short purchases (doesn't understand the
  latter)
- there are probably cases outside the current unit tests that this fails for


## 2. capital_gains_classifier:

Classifies sales into losses and gains (NOT into long and short).

Rewrites transactions from an account like:
Capital-Gains:Account

into:

Capital-Gains:Losses:Account
Capital-Gains:Gains:Account

based on whether the posting into that account is positive or negative.

WARNINGS:
- still under development
