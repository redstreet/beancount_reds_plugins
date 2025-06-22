# beancount-reds-plugins

A collection of plugins for [Beancount](https://beancount.github.io/), software for
[plain text, double entry bookkeeping](https://plaintextaccounting.org/).
See README.md in individual directories for plugin specific documentation.

## Plugin list:
- __[autoclose_tree](https://github.com/redstreet/beancount_reds_plugins/tree/master/beancount_reds_plugins/autoclose_tree#readme)__:
  automatically closes all of an account's descendants when an account is closed.
- __[capital_gains_classifier](https://github.com/redstreet/beancount_reds_plugins/tree/master/beancount_reds_plugins/capital_gains_classifier#readme)__:
  rebooks capital gains into separate long and short accounts, and separate gains and
  losses accounts
- __[effective_date](https://github.com/redstreet/beancount_reds_plugins/tree/master/beancount_reds_plugins/effective_date#readme)__:
  enables per-posting dates (each posting in a transaction can have a different date)
- __[opengroup](https://github.com/redstreet/beancount_reds_plugins/tree/master/beancount_reds_plugins/opengroup#readme)__:
  Inserts open statements for sets of accounts based on specifiable rules.
- __[rename_accounts](https://github.com/redstreet/beancount_reds_plugins/tree/master/beancount_reds_plugins/rename_accounts#readme)__:
  rename arbitrary accounts on the fly (eg: move Taxes from Expenses to Income when you
  temporarily want to view all your Expenses except taxes)
- __[zerosum](https://github.com/redstreet/beancount_reds_plugins/tree/master/beancount_reds_plugins/zerosum#readme)__:
  find matching pairs of postings that sum up to zero. Useful in de-duplication, and
  tracking things such as reimbursements, rebates, etc.

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

### Disabling plugins during the import process

In general, no plugins should run on the source files that are passed to
`smart_importer`. Here's [an article](https://reds-rants.netlify.app/personal-finance/automatically-categorizing-postings/)
that shows how.

In short (this is for `zsh`, adapt to your shell as needed):
```
bean-extract my.import -f <(echo 'plugin "beancount.plugins.auto_accounts"'; cat ${INGEST_ROOT}/../source/*) $file
```
