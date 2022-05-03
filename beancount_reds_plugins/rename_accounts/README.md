## rename_accounts plugin for Beancount

Plugin that renames accounts, given a list of account pairs to rename. This enables you
to temporarily modify your account hierarchy.

This is useful when one wants two different views (reports) into your ledger. Renames
can be turned on or off relatively easily (by manually commenting them out in your
Beancount plugin directive) depending on the type of reporting desired. Here is an
example where this comes in handy:

```
Expenses:Taxes ---rename--> Income:Taxes
```

Taxes are always booked as expenses. However:
- without the rename, of course, the `Income` account is gross income, and `Expenses`
  includes taxes
- with the rename, the `Income` account shows the net (after-tax) income. More
  interestingly, the renames avoids Expense reports from being cluttered and dominated
  by taxes (thus rendering them less useful)


Here are a [few other examples](https://groups.google.com/g/beancount/c/ZD8701xPE3Y/m/M0mA0gb1AgAJ) from the
Beancount mailing list where renaming accounts helps switch between a cash flow view and
a tax view.

Of course, the right set of queries can also give you these reports. However, renaming
allows you to take advantage of standard, built-in reporting tools and UIs, which are
far more extensive than queries. For example, Fava's UI hierarchy and associated
visualizations (treemaps, sunburst plots, bar plots across time, changes by year, etc.)
are not available for queries. Renaming solves this problem.


## Configuring

Example to include in your beancount file:

```python
plugin "beancount_reds_plugins.rename_accounts.rename_accounts" "{
 'Expenses:Taxes' : 'Income:Taxes',
 'Assets:House:Capital-Improvements' : 'Expenses:House:Appliances',
 }"
```

The strings on the left specify substrings, which are matched against accounts. Here is
a pseudocode example to clarify:

```python
if 'Expenses:Taxes' in account:
    account = account.replace('Expenses:Taxes', 'Income:Taxes')
```

Therefore, `Expenses:Taxes:Federal` will be renamed to `Income:Taxes:Federal` in the
example above.

Account opening entries will be added to Beancount automatically if needed (eg: for
`Income:Taxes:Federal` above).
