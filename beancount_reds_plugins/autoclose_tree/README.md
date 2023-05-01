NOTE: this plugin has now been merged into [Beancount](https://github.com/beancount/beancount/pull/751) and will no longer be
maintained here.

## autoclose_tree plugin for Beancount

Automatically closes all of an account's descendants when an account is closed. For
example, turns this:

```
2014-01-01 open Assets:XBank
2014-01-01 open Assets:XBank:AAPL
2014-01-01 open Assets:XBank:AAPL:Fuji
2015-01-01 close Assets:XBank
```

into:

```
2014-01-01 open Assets:XBank
2014-01-01 open Assets:XBank:AAPL
2014-01-01 open Assets:XBank:AAPL:Fuji
2015-01-01 close Assets:XBank
2015-01-01 close Assets:XBank:AAPL
2015-01-01 close Assets:XBank:AAPL:Fuji
```

You can close unopened parents:
```
2017-11-10 open Assets:Brokerage:AAPL
2017-11-10 open Assets:Brokerage:ORNG
2018-11-10 close Assets:Brokerage  ; this account was never opened, and this would
                                   ; normally be an invalid directive
```

becomes:

```
2017-11-10 open Assets:Brokerage:AAPL
2017-11-10 open Assets:Brokerage:ORNG
2018-11-10 close Assets:Brokerage:AAPL
2018-11-10 close Assets:Brokerage:ORNG
```


Any explicitly specified close is left untouched. For example:


```
2014-01-01 open Assets:XBank
2014-01-01 open Assets:XBank:AAPL
2014-01-01 open Assets:XBank:AAPL:Fuji
2015-01-01 close Assets:XBank:AAPL
2016-01-01 close Assets:XBank
```

becomes:

```
2014-01-01 open Assets:XBank
2014-01-01 open Assets:XBank:AAPL
2014-01-01 open Assets:XBank:AAPL:Fuji
2015-01-01 close Assets:XBank:AAPL
2015-01-01 close Assets:XBank:AAPL:Fuji
2016-01-01 close Assets:XBank
```



## Setup
Include in your beancount file:
```
plugin "beancount_reds_plugins.autoclose_tree.autoclose_tree"
```

Include the line above _after_ any plugins that generate `open` directives for accounts
you want to auto close. For example, the `auto_accounts` plugin that ships with
Beancount:

```
plugin "beancount.plugins.auto_accounts"
plugin "beancount_reds_plugins.autoclose_tree.autoclose_tree"
```

There is no configuration.
