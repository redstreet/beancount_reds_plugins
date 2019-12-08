Effective dates plugin for Beancount
------------------------------------

Plugin to rename accounts. Takes a list of account pairs to rename. Here are some
examples where this can be useful.

This is useful when one wants two different views (reports) into the same set of
transactions. Renames in this plugin can be easily turned on or off (by manually
commenting them out in your beancount plugin directive) depending on the type of
reporting desired. Here is an example where this is useful:

1. Expenses:Taxes -> Income:Taxes

This rename allows taxes to avoid cluttering and dominating the Expense reports (and
thus rendering them less useful), and simultaneously reports net (after-tax) income.
Without the rename, of course, the view of gross income and expenses including taxes
becomes available.

Of course, the right set of queries can also give you these reports renaming. However,
renaming allows you to take advantage of standard, built-in reporting tools. For
example, fava's treemap/sunburst expense plots would not work out of the box on a
custom query. Renaming solves this problem.
