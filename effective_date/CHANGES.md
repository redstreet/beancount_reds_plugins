2020-02-29
Per-posting effective dates:
- This is a breaking change! The previous incarnation of this plugin used the
  `effective_date` metadata field from a transaction. This was a hack. The cleaned up
  version now uses the same field associated with postings.

- The older plugin is retained in the 'effective_date_transaction' function, which is
  disabled by default but can optionally be turned on.

