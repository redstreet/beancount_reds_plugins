# Capital gains classifier plugin for Beancount
---------------------------------------------

--------------------------------------------------
## This plugin is Experimental / under development
--------------------------------------------------

Classifies sales into losses and gains (NOT into long and short).

Rewrites transactions from an account like:
Capital-Gains:Long:Account

into:

Capital-Gains:Long:Losses:Account
Capital-Gains:Long:Gains:Account

based on whether the posting into that account is positive or negative.

