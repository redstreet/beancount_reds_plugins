PREFIX_LEN = 2


class LinkMaker():
    def __init__(self, formats):
        self.date_format = formats['DATE_FORMAT']
        self.link_format = formats['LINK_FORMAT']
        self.base = int(formats['SEQUENCE_BASE'])
        self.case = formats['SEQUENCE_CASE']
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

        if self.case == 'capitalize':
            cased = stripped.capitalize()
        elif self.case == 'lower':
            cased = stripped.lower()
        elif self.case == 'title':
            cased = stripped.title()
        elif self.case == 'upper':
            cased = stripped.upper()
        else:
            raise ValueError(f"Invalid case: {self.case}")

        filled = cased.zfill(self.zfill)
        return filled

    def counter(self, key):
        count = self.counters.get(key, 0)
        self.counters[key] = count + 1
        return count

    def get(self, entry_date):
        date_str = entry_date.strftime(self.date_format)
        # Because some date formats map multiple dates to a single string (or
        # even ~all~ dates to a single string if the date format is an empty
        # string), the counters must be keyed by date_str, not the date value.
        count = self.counter(date_str)
        seq = self.format(count)

        link = self.link_format.format(date=date_str, seq=seq)
        return link
