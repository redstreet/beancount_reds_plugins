## EXPERIMENTAL opengroup plugin for Beancount: (UNDER EARLY DEVELOPMENT)

Inserts `open` statements for a set of accounts based on rules. For example, turns:

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

The above uses the 'commodity_leaves_default_booking' ruleset.

## Why use this plugin?

If you like the benefit of a layer of error checking that you get by manually opening
and closing accounts in Beancount, this plugin offers a way to get that benefit while
being compact and consistent in your account declarations. Opening groups of accounts
based on metadata like the above helps with:

- ensuring your accounts follow consistent naming conventions
- expression density (fewer open statements)
- ease of adding new funds (no need to remember all the corresponding accounts to open
  and their conventions; simply add the new ticker to the metadata list)

## Limitations

1. Custom booking methods cannot be specified via this plugin since all plugins run
   after booking is done in Beancount. If you use different booking methods for
   different accounts, you can only opengroup your global default via this plugin,
   specified like so in your source:
   ```
   option "booking_method" "STRICT"
   ```
   
   For the remaining accounts, use `opengroup_commodity_leaves`, which does not include the
   Asset account above, which you can then open manually.

2. Rulesets are currently hardcoded. TODO: make it generic, based on specifiable sets of
rules
   - eg: "opengroup_commodity_leaves" would be a rule that opens a specific set of
     accounts
   - easier expressed as python code than string rules?

