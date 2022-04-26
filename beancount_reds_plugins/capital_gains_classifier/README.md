# Capital gains classifier plugin for Beancount

## WARNING: These plugins are experimental / under development

There are two plugins included here. See the respective `.py` files for info on how to
configure them:

## 1. long_short:
Classifies sales into short term or long term capital gains based on how long they have
been held.

WARNING: still under development; doesn't work for leap years yet. There are probably
lots of other cases outside the current unit tests that this fails for.


## 2. capital_gains_classifier:

Classifies sales into losses and gains (NOT into long and short).

Rewrites transactions from an account like:
Capital-Gains:Account

into:

Capital-Gains:Losses:Account
Capital-Gains:Gains:Account

based on whether the posting into that account is positive or negative.

