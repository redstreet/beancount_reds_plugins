## autoclose_tree plugin for Beancount

Automatically closes all of an account's descendants when an account is closed. For
example, turns this:

```
2014-01-01 open Assets:XBank
2014-01-01 open Assets:XBank:AAPL
2014-01-01 open Assets:XBank:AAPL:Fuji
2014-01-01 open Assets:XBank:AAPL:Gala
2014-01-01 open Assets:XBank:ORNG
2014-01-01 open Assets:XBank:BANANA
2015-01-01 close Assets:XBank
```

into:

```
2014-01-01 open Assets:XBank
2014-01-01 open Assets:XBank:AAPL
2014-01-01 open Assets:XBank:AAPL:Fuji
2014-01-01 open Assets:XBank:AAPL:Gala
2014-01-01 open Assets:XBank:ORNG
2014-01-01 open Assets:XBank:BANANA
2015-01-01 close Assets:XBank
2015-01-01 close Assets:XBank:AAPL
2015-01-01 close Assets:XBank:AAPL:Fuji
2015-01-01 close Assets:XBank:AAPL:Gala
2015-01-01 close Assets:XBank:ORNG
2015-01-01 close Assets:XBank:BANANA
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
plugin "beancount_reds_plugins.autoclose_tree.autoclose_tree" "{}"
```

There is no configuration.
