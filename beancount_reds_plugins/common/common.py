#!/usr/bin/env python3
"""Common code for beancount_reds_plugins"""

from beancount.core import data
from beancount.core import getters


def create_open_directives(new_accounts, entries, meta_desc='<beancount_reds_plugins_common>'):
    """Create open entries that don't already exist"""
    if not entries:
        return []

    meta = data.new_metadata(meta_desc, 0)
    earliest_date = entries[0].date
    open_entries = getters.get_account_open_close(entries)
    new_open_entries = []
    for account_ in sorted(new_accounts):
        if account_ not in open_entries:
            meta = data.new_metadata(meta['filename'], 0)
            open_entry = data.Open(meta, earliest_date, account_, None, None)
            new_open_entries.append(open_entry)
    return new_open_entries
