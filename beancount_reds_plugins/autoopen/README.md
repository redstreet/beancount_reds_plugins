## EXPERIMENTAL autoopen plugin for Beancount: (UNDER EARLY DEVELOPMENT)

Automatically opens a set of accounts based on rules. For example, turns:

```
2000-01-01 open Assets:Investments:Taxable:Midelity PARENT
  autoopen_commodity_leaves_default_booking: "ABC,DEFGH"
```

into:

```
2000-01-01 open Assets:Investments:Taxable:Midelity PARENT

2000-01-01 open Assets:Investments:Taxable:Midelity:ABC
2000-01-01 open Income:Investments:Taxable:Dividends:Midelity:ABC       USD
2000-01-01 open Income:Investments:Taxable:Interest:Midelity:ABC       USD
2000-01-01 open Income:Investments:Taxable:Capital-Gains:Midelity:ABC   USD
2000-01-01 open Income:Investments:Taxable:Capital-Gains-Distributions:Short:Midelity:ABC   USD
2000-01-01 open Income:Investments:Taxable:Capital-Gains-Distributions:Long:Midelity:ABC   USD

```

The above uses the 'commodity_leaves_default_booking' ruleset.

## Why use this plugin?

- to ensure your accounts follow consistent naming conventions
- expression density (fewer open lines)
- ease of adding new funds (no need to remember all the corresponding accounts to open.
  Simply add the ticker to the metadata list)

## Limitations

TODO:
1. Custom booking methods cannot be specified via this plugin since all plugins run
   after booking is done in Beancount. If you use different booking methods for
   different accounts, you can only autoopen your global default via this plugin,
   specified like so in your source:
   ```
   option "booking_method" "STRICT"
   ```
   
   For the remaining accounts, use `autoopen_commodity_leaves`, which does not include the
   Asset account above, which you can then open manually.

2. Rulesets are currently hardcoded. Make it generic, based on specifiable sets of rules
   - eg: "autoopen_commodity_leaves" would be a rule that opens a specific set of accounts
   - easier expressed as python code than some string rules

