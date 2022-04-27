__copyright__ = "Copyright (C) 2020  Red S"
__license__ = "GNU GPLv3"

import unittest
import re

from beancount_reds_plugins.effective_date.effective_date import effective_date
from beancount.core import data
from beancount.parser import options
from beancount import loader
import datetime


def get_entries_with_narration(entries, regexp):
    """Return the entries whose narration matches the regexp.

    Args:
      entries: A list of directives.
      regexp: A regular expression string, to be matched against the
        narration field of transactions.
    Returns:
      A list of directives.
    """
    return [entry
            for entry in entries
            if (isinstance(entry, data.Transaction) and
                re.search(regexp, entry.narration))]


class TestEffectiveDate(unittest.TestCase):

    def test_empty_entries(self):
        entries, _ = effective_date([], options.OPTIONS_DEFAULTS.copy(), None)
        self.assertEqual([], entries)

    @loader.load_doc()
    def test_no_effective_dates(self, entries, _, options_map):
        """
        2014-01-01 open Liabilities:Mastercard
        2014-01-01 open Expenses:Taxes:Federal

        2014-02-01 * "Estimated taxes for 2013"
          Liabilities:Mastercard    -2000 USD
          Expenses:Taxes:Federal  2000 USD
         """
        new_entries, _ = effective_date(entries, options_map, None)
        self.assertEqual(new_entries, entries)

    @loader.load_doc()
    def test_expense_earlier(self, entries, _, options_map):
        """
        2014-01-01 open Liabilities:Mastercard
        2014-01-01 open Expenses:Taxes:Federal

        2014-02-01 * "Estimated taxes for 2013"
          Liabilities:Mastercard    -2000 USD
          Expenses:Taxes:Federal  2000 USD
            effective_date: 2013-12-31
        """

        # Above should turn into:
        # 2014-02-01 "Estimated taxes for 2013"
        #   Liabilities:Mastercard     -2000 USD
        #   Liabilities:Hold:Taxes:Federal 2000 USD

        # 2013-12-31 "Estimated taxes for 2013"
        #   Liabilities:Hold:Taxes:Federal    -2000 USD
        #   Expenses:Taxes:Federal    2000 USD

        new_entries, _ = effective_date(entries, options_map, None)
        self.assertEqual(5, len(new_entries))

        results = get_entries_with_narration(new_entries, "Estimated taxes")
        self.assertEqual(datetime.date(2013, 12, 31), results[0].date)
        self.assertEqual(datetime.date(2014, 2, 1), results[1].date)

        # self.assertEqual('Assets:Account1', results.postings[0].account)
        # self.assertEqual('Income:Account1', results.postings[1].account)

        # mansion = get_entries_with_narration(new_entries, "units of MANSION")[0]
        # self.assertEqual(2, len(mansion.postings))
        # self.assertEqual(D('-100'), mansion.postings[0].units.number)

        # entry = get_entries_with_narration(unreal_entries, '3 units')[0]
        # self.assertEqual("Equity:Account1:Gains", entry.postings[0].account)
        # self.assertEqual("Income:Account1:Gains", entry.postings[1].account)
        # self.assertEqual(D("24.00"), entry.postings[0].units.number)
        # self.assertEqual(D("-24.00"), entry.postings[1].units.number)

#    def test_expense_later(self, entries, _, options_map):
#        """
#        2014-01-01 open Liabilities:Mastercard
#        2014-01-01 open Expenses:Rent
#
#        2014-02-01 "Rent"
#          Liabilities:Mastercard    -2000 USD
#          Expenses:Rent              2000 USD
#            effective_date: 2014-05-01
#        """
#
#        # Above should turn into:
#        # 2014-02-01 "Rent"
#        #   Liabilities:Mastercard     -2000 USD
#        #   Liabilities:Hold:Rent 2000 USD
#
#        # 2014-05-01 "Rent"
#        #   Liabilities:Hold:Rent -2000 USD
#        #   Expenses:Rent     2000 USD

    @loader.load_doc()
    def test_expense_later_multiple(self, entries, _, options_map):
        """
        2014-01-01 open Liabilities:Mastercard
        2014-01-01 open Expenses:Car:Insurance

        2014-02-01 * "Car insurance: 3 months"
          Liabilities:Mastercard    -600 USD
          Expenses:Car:Insurance     200 USD
            effective_date: 2014-03-01
          Expenses:Car:Insurance     200 USD
            effective_date: 2014-04-01
          Expenses:Car:Insurance     200 USD
            effective_date: 2014-05-01
        """

        # Above should turn into:
        # 2014-02-01 "Car insurance: 3 months"
        #   Liabilities:Mastercard         -600 USD
        #   Liabilities:Hold:Car:Insurance  600 USD
        #
        # 2014-03-01 "Car insurance: 3 months"
        #   Assets:Hold:Car:Insurance -200 USD
        #   Expenses:Car:Insurance     200 USD
        #
        # 2014-04-01 "Car insurance: 3 months"
        #   Assets:Hold:Car:Insurance -200 USD
        #   Expenses:Car:Insurance     200 USD
        #
        # 2014-05-01 "Car insurance: 3 months"
        #   Assets:Hold:Car:Insurance -200 USD
        #   Expenses:Car:Insurance     200 USD

        new_entries, _ = effective_date(entries, options_map, None)
        self.assertEqual(7, len(new_entries))
