# Changelog


## 0.3.0 (2023-01-24)


### New
- autoclose_tree: new plugin automatically closes all of an account's descendants when
  an account is closed. [Red S]
- opengroup (experimental): new plugin to automatically open sets of accounts. [Red S]

### Improvements
- rename_accounts: accept regexes for renames (#20) [Ankur Dave]
- rename_accounts: Support renaming within all directives, not just Transaction (#17) [Ankur Dave]
- rename_accounts: Copy only renamed directives for performance (#18) [Ankur Dave]
- long_short: use tolerance to determine whether to scale. [Red S]

### Fixes
- #19 error when used in conjunction with beancount.plugins.auto_accounts. [Red S]



## 0.2.0 (2021-04-30)
### New plugins
- capital gains long/short classifier. [Red S]
- capital gains gain/loss classifier [Red S]

### Improvements
- long_short: use tolerance to determine whether to scale. [Red S]
- long_short now works for short positions. [Red S]
- rename capital_gains_classifier to gain_loss. [Red S]

### Fixes
- rename_accounts: fixed loop code. [Red S]

### Other
- doc: add changelog, gitchangelog config. [Red S]
- doc: readme. [Red S]
- long_short: refactor for clarity. [Red S]
- refactor: create_open_directives() [Red S]

## 0.1.1 (2021-02-05)


### Fixes

- fix: don't match with the same exact posting. [Jason Kim]

### Other

- flake. [Red S]
- zerosum: add config option "tolerance" (#16) [Jason Kim]

  * style: s/Vsia/Visa/g

  * style: trim trailing whitespace for two files

  * test: add two new unit tests in prep for tolerance

  In preparation of the "tolerance" config option feature, add two new
  unit tests:

  - `test_two_matched_below_epsilon`: demonstrate that two transactions
    that logically shouldn't match can end up matching because they sum up
    to be below epsilon (aka tolerance)
  - `test_two_unmatched_above_epsilon`: prepare to demonstrate that two
    transactions that logically shouldn't match can avoid matching if
    epsilon (aka tolerance) is set low enough (this test should currently
    fail because tolerance is too high!)

  * feat: add epsilon_delta as config parameter

  * style: S/epsilon_delta/tolerance/g

  * style: s/TOLERANCE/DEFAULT_TOLERANCE/

  * style: add trailing comma to config dict

  * test: set tolerance to 0.0098

  Set tolerance slightly lower so that `test_two_unmatched_above_epsilon`
  lives up to its name and now passes.

  * style: s/Visa/Green/
- add unittests from @jaki. [Red S]
- style: clarify which txns shouldn't error. [Jason Kim]
- Revert "style: add comments to clarify postings match" [Jason Kim]

  This reverts commit 1eb6edb1f415b263cf33e2cfc82ed3ec52138c70.
- test: make the lookalike test more accurate. [Jason Kim]
- test: test lookalike postings. [Jason Kim]

  Make sure that lookalike postings aren't considered identical so that
  a match is attempted.  In the code, this exercises `p is posting`.
- style: rm extra space before - [Jason Kim]
- style: add comments to clarify postings match. [Jason Kim]
- style: make date uniform jan 1. [Jason Kim]
- test: add case where both postings match in one tx. [Jason Kim]

  Protect against regression by making sure that two distinct postings
  within the same transaction can match.
- test: add failing test case with low-cost txn. [Jason Kim]
- add unit tests for zerosum; test for #15. [Red S]
- add unittest for rename_accounts. [Red S]
- Update path. [Red S]
- Remove non-pip. [Red S]
- Update zerosum-example.beancount. [Red S]

## 0.1.0 (2020-05-04)


### Other

- Create pythonpublish.yml. [Red S]
- readme updates for pypi. [Red S]
- Redo dirs for PyPI. [Red S]
- add new plugin: capital gains classifier (into gains/losses) [Red S]
- Fix formatting issues in docs. [Martin Michlmayr]
- Fix typos (#11) [Red S]
- Merge pull request #10 from redstreet/eff_date_per_posting. [Red S]

  Eff date per posting
- cleanup. [Red S]
- added human readable link (thanks justus pendleton for the suggestion) [Red S]
- Merge pull request #9 from redstreet/eff_date_per_posting. [Red S]

  add CHANGES.md
- add CHANGES.md. [Red S]
- Merge pull request #8 from redstreet/eff_date_per_posting. [Red S]

  Effective date per posting
- effective_date README update for per posting. [Red S]
- add beancount links to link original and effective date transactions! [Red S]
- add operating currency for fava. [Red S]
- Disable old transaction-level hacky effective date. [Red S]
- cleanup. [Red S]
- effective_date example beancount source. [Red S]
- gitignore. [Red S]
- Test skeleton. [Red S]
- Commented out debug prints. [Red S]
- Add per posting effective date. [Red S]
- Effective date: recognizing income earlier. [Red S]
- Merge pull request #7 from redstreet/docs. [Red S]

  drat. README title
- drat. README title. [Red S]
- Merge pull request #6 from redstreet/docs. [Red S]

  more README updates
- more README updates. [Red S]
- Merge pull request #5 from redstreet/docs. [Red S]

  add example to README
- add example to README. [Red S]
- Merge pull request #4 from redstreet/docs. [Red S]

  Updated README.
- Updated README. [Red S]
- Merge branch 'zerosum_performance' [Red S]
- Zerosum: minor refactoring and cleanup. [Red S]
- Rename plugin can now do arbitrary renames. [Red S]
- Merge pull request #3 from redstreet/zerosum_performance. [Red S]

  Zerosum performance
- Cleanup zerosum. [Red S]
- Refactored zerosum for 4x-6x performance improvement. [Red S]

  - Rewrote match finder: the previous match finder iterated through all
  entries in the given account. Updated to match forward only and break
  upon exceeding the date range (entry list is sorted by date by
  beancount)

  - Pre-build finding entries of interest so the entire set of entries is
  iterated only once

  - cprofile within DEBUG
- Merge pull request #2 from wzyboy/zerosum-mark-unmatched. [Red S]
- Flag transactions, but default off. [Zhuoyun Wei]
- Fix TypeError when account_name_replace is not in config. [Zhuoyun Wei]
- zerosum: Mark unmatched txn. [Zhuoyun Wei]
- PEP8. [Zhuoyun Wei]
- Print stats conditionally on DEBUG being set. [Red S]
- README: cleanup and conversion to markdown. [Red S]
- Merge branch 'master' of github.com:redstreet/beancount_plugins_redstreet. [Red S]
- Merge branch 'master' of github.com:redstreet/beancount_plugins_redstreet. [Red S]
- Merge pull request #1 from wzyboy/patch-1. [Red S]

  Fix Markdown rendering.
- Update README.md. [Zhuoyun Wei]
- Add 'account_name_replace' option in config. [Red S]

  Allows target account name for matched accounts to be skipped in the
  config (specified as an empty string), and instead be constructed by
  the specified string replacement
- upstream changes. [Red S]
- Added rename accounts plugin. [Red S]
- update README. [Red S]
- fixes to match upstream API changes (ref: beancount/2016-02-06) [Red S]
- Reorganized directories. [Red S]
- Added effective date plugin. [Red S]
- Fixes to match upstream API changes (in beancount) [Red S]

  Reference: see beancount/CHANGES, under 2015-07-11. The back reference datastructure was
  removed. Updated plugin to make it work with the new data structure. Might have to see
  if a clean up is needed.
- Initial commit. [Red S]


## 0.1.1 (2021-02-05)

### Fixes
- Fix: don't match with the same exact posting. [Jason Kim]


### Improvements
- Zerosum: add config option "tolerance" (#16) [Jason Kim]
  - feat: add epsilon_delta as config parameter

### Other
- Style: clarify which txns shouldn't error. [Jason Kim]
- Tests: various[Jason Kim]
- Tests: zerosum; test for #15.
- Tests: rename_accounts
- Tests: unittests from @jaki.

