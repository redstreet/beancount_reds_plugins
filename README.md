# beancount-reds-plugins
A collection of plugins for Beancount double entry accounting. Each directory contains a
plugin for [Beancount](http://furius.ca/beancount/). See README.md in individual
directories for plugin descriptions.

## Plugin list:
- effective_date: enables per-posting dates (each posting in a transaction can have a
  different date)
- rename_accounts: rename arbitrary accounts on the fly (eg: move Taxes from Expenses to
  Income when you temporarily want to view all your Expenses except taxes)
- zerosum: find matching paris of postings that sum up to zero. Useful in
  de-duplication, and tracking things such as reimbursements, rebates, etc.
- capital_gains_classifier (experimental): rewrites capital gains into separate accounts
  for gains and losses

## Installation
`pip3 install beancount-reds-plugins`

Or to install the bleeding edge version from git:
`pip3 install git+https://github.com/redstreet/beancount_reds_plugins`

## Usage
Invoke and configure a plugin by including it in your beancount source. For example,
invoke the `rename_accounts` plugin like so:

```python
plugin "beancount_reds_plugins.rename_accounts.rename_accounts" "{
 'Expenses:Taxes' : 'Income:Taxes',
 }"
```
See README.md in individual directories for how to configure each plugin.
