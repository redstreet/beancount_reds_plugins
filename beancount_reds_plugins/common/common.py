#!/usr/bin/env python3
"""Common code for beancount_reds_plugins"""

from beancount.core import data
from beancount.core import getters

PREFIX_LEN = 2


def create_open_directives(new_accounts, entries,
                           meta_desc='<beancount_reds_plugins_common>'):
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


class LinkMaker():
    def __init__(self, link_format, base, date_format=None, zfill=None):
        self.link_format = link_format
        self.base = int(base)
        self.date_format = date_format
        self.zfill = int(zfill)
        self.counters = {}

    def format(self, x):
        if self.base == 8:
            stripped = oct(x)[PREFIX_LEN:]
        elif self.base == 10:
            stripped = str(x)
        elif self.base == 16:
            stripped = hex(x)[PREFIX_LEN:]
        else:
            raise ValueError(f"Unsupported base: {self.base}")

        filled = stripped.zfill(self.zfill)
        return filled

    def counter(self, key):
        count = self.counters.get(key, 0)
        self.counters[key] = count + 1
        return count

    def get(self, entry_date):
        date_str = entry_date.strftime(self.date_format)
        # The date format may be set to only a year or just an empty string,
        # so, to guarantee uniqueness, the counters must be keyed by date_str,
        # not the date value.
        count = self.counter(date_str)
        seq = self.format(count)

        link = self.link_format.format(date=date_str, seq=seq)
        return link
