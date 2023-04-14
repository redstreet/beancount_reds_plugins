# Opengroup: an EXPERIMENTAL plugin for Beancount

Inserts `open` statements for a set of accounts based on specified rules. For example,
turns:

```
2000-01-01 open Assets:Investments:Taxable:Midelity PARENT
  opengroup_cash_and_fees: "USD"
  opengroup_commodity_leaves_default_booking: "AAPL,VTI"
  opengroup_commodity_leaves_cgdists: "VTI"
```

into:

```
2000-01-01 open Assets:Investments:Taxable:Midelity PARENT

2000-01-01 open Assets:Investments:Taxable:Midelity:USD USD
2000-01-01 open Expenses:Fees-and-Charges:Brokerage-Fees:Taxable:Midelity USD

2000-01-01 open Assets:Investments:Taxable:Midelity:AAPL
2000-01-01 open Income:Investments:Taxable:Dividends:Midelity:AAPL     USD
2000-01-01 open Income:Investments:Taxable:Interest:Midelity:AAPL      USD
2000-01-01 open Income:Investments:Taxable:Capital-Gains:Midelity:AAPL USD

2000-01-01 open Assets:Investments:Taxable:Midelity:VTI
2000-01-01 open Income:Investments:Taxable:Dividends:Midelity:VTI      USD
2000-01-01 open Income:Investments:Taxable:Interest:Midelity:VTI       USD
2000-01-01 open Income:Investments:Taxable:Capital-Gains:Midelity:VTI  USD

2000-01-01 open Income:Investments:Taxable:Capital-Gains-Distributions:Short:Midelity:VTI USD
2000-01-01 open Income:Investments:Taxable:Capital-Gains-Distributions:Long:Midelity:VTI  USD
```

### Why use this plugin?

If you like the benefit of a layer of error checking that you get by manually opening
and closing accounts in Beancount, this plugin offers a way to get that benefit while
being compact and consistent in your account declarations. Opening groups of accounts
based on metadata like the above helps with:

- ensuring your accounts follow consistent naming conventions
- expression density (fewer open statements)
- ease of adding new funds (no need to remember all the corresponding accounts to open
  and their conventions; simply add the new ticker to the metadata list)

### Plugin Invoking and Configuration

A default config is built in. To invoke the plugin with the default config, use this in
your Beancount source:

```
plugin "beancount_reds_plugins.opengroup.opengroup" "{}"
```

Config format is below if you would like to write your own config:


```
plugin "beancount_reds_plugins.opengroup.opengroup" """{
  <rule_name>: (
    <regex_with_named_groups>,

    [(<account_to_open>, <comma_separated_currencies>),
     ...
    ]),
    
  <rule_name>: (
  ...
  )
  
}"""
```
    
All variables above are strings. Special variables are:
- `f_acct`: entire original account name (for which the `opengroup_` metadata was
  specified)
- `f_ticker`: ticker from the list (eg: AAPL, VTI, etc. from the example on the top)
- `f_opcurr`: operating currency declared in the Beancount file, if there was one
  (defaults to USD)

See default config below for an example config. 

### Default Config

The config for the example on the top was the default, built-in config, which looks like:

```
default_rules = {
  'cash_and_fees': (  # Open cash and fees accounts
    '(?P<root>[^:]*):(?P<subroot>[^:]*):(?P<taxability>[^:]*):(?P<account_name>.*)',

    [('{f_acct}:{f_ticker}', '{f_opcurr}'),
     ('Expenses:Fees-and-Charges:Brokerage-Fees:{taxability}:{account_name}', '{f_opcurr}'),
    ]),

  'commodity_leaves_income': (  # Open common set of investment accounts with commodity leaves
    '(?P<root>[^:]*):(?P<subroot>[^:]*):(?P<taxability>[^:]*):(?P<account_name>.*)',

    [('Income:{subroot}:{taxability}:Dividends:{account_name}:{f_ticker}',     '{f_opcurr}'),
     ('Income:{subroot}:{taxability}:Interest:{account_name}:{f_ticker}',      '{f_opcurr}'),
     ('Income:{subroot}:{taxability}:Capital-Gains:{account_name}:{f_ticker}', '{f_opcurr}'),
    ]),

  'commodity_leaves_income_and_asset': (  # Open commodity_leaves_income + asset account for the ticker (default booking)
    '(?P<root>[^:]*):(?P<subroot>[^:]*):(?P<taxability>[^:]*):(?P<account_name>.*)',

    [('{f_acct}:{f_ticker}',                                                   '{f_ticker}'),
     ('Income:{subroot}:{taxability}:Dividends:{account_name}:{f_ticker}',     '{f_opcurr}'),
     ('Income:{subroot}:{taxability}:Interest:{account_name}:{f_ticker}',      '{f_opcurr}'),
     ('Income:{subroot}:{taxability}:Capital-Gains:{account_name}:{f_ticker}', '{f_opcurr}'),
    ]),

  'commodity_leaves_cgdists':  # Open capital gains distributions accounts
    ('(?P<root>[^:]*):(?P<subroot>[^:]*):(?P<taxability>[^:]*):(?P<account_name>.*)',

    [('Income:{subroot}:{taxability}:Capital-Gains-Distributions:Long:{account_name}:{f_ticker}',  '{f_opcurr}'),
     ('Income:{subroot}:{taxability}:Capital-Gains-Distributions:Short:{account_name}:{f_ticker}', '{f_opcurr}'),
    ]),
}
```

### Limitations

- Custom booking methods cannot be specified via this plugin since all plugins run after
  booking is done in Beancount. If you use different booking methods for different
  accounts, you can only opengroup your global default via this plugin, specified like so
  in your source:
     
  ```
  option "booking_method" "STRICT"
  ```
     
  For the remaining accounts, use `opengroup_commodity_leaves`, which does not include the
  Asset account above, which you can then open manually.

- Closing account sets: (TBD: write a plugin to automatically close account sets).
  Meanwhile, [autoclose_tree](https://github.com/redstreet/beancount_reds_plugins/tree/main/beancount_reds_plugins/autoclose_tree#readme)
  can be used in conjunction with this plugin to close a tree of accounts.
