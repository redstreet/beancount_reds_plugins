## autoopen plugin for Beancount: EXPERIMENTAL / UNDER DEVELOPMENT

Automatically opens a set of accounts based on rules. For example, turns:

```
2000-01-01 open Assets:Investments:Taxable:Midelity PARENT
  autoopen_commodity_leaves: "ABC,DEFGH"
```

into:

```
2000-01-01 open Assets:Investments:Taxable:Midelity PARENT

2000-01-01 open Assets:Investments:Taxable:Midelity:ABC                 "STRICT"
2000-01-01 open Income:Investments:Taxable:Dividends:Midelity:ABC       USD
2000-01-01 open Income:Investments:Taxable:Interest:Midelity:ABC       USD
2000-01-01 open Income:Investments:Taxable:Capital-Gains:Midelity:ABC   USD
2000-01-01 open Income:Investments:Taxable:Capital-Gains-Distributions:Short:Midelity:ABC   USD
2000-01-01 open Income:Investments:Taxable:Capital-Gains-Distributions:Long:Midelity:ABC   USD

```

TODO:
- Account set is currently hardcoded. Make it generic, based on specifiable sets of rules
  - eg: "autoopen_commodity_leaves" would be a rule that opens a specific set of accounts
  - easier expressed as python code than some string rules
