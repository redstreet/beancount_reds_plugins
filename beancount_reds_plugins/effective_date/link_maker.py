LINK_FORMAT = 'edate-{date}-{seq}'
PREFIX_LEN = 2


class LinkMaker():
    def __init__(self, formats):
        self.date_format = formats['DATE_FORMAT']
        self.base = int(formats['SEQUENCE_BASE'])
        self.zfill = int(formats['SEQUENCE_ZFILL'])
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

        link = LINK_FORMAT.format(date=date_str, seq=seq)
        return link
