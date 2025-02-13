from random import shuffle


HEX_BASE = 16


class LinkMaker():
    def __init__(self, formats):
        self.date_format = formats['DATE_FORMAT']
        self.link_format = formats['LINK_FORMAT']
        self.rand_len = formats['RANDOM_LEN']
        self.rand_gens = {}

    def hexformat(self, i):
        return hex(i)[2:].zfill(self.rand_len)

    def rand_counter(self, n=10, repr_func=int):
        values = [x for x in range(n)]
        shuffle(values)
        i = 0

        while i < n:
            value = values[i]
            i += 1
            yield repr_func(value)

    def get(self, entry_date):
        date_str = entry_date.strftime(self.date_format)

        if date_str not in self.rand_gens:
            n = HEX_BASE**self.rand_len
            repr_func = self.hexformat
            self.rand_gens[date_str] = self.rand_counter(n, repr_func)
        rand_str = next(self.rand_gens[date_str])

        link = self.link_format.format(date=date_str, rand=rand_str)
        return link
