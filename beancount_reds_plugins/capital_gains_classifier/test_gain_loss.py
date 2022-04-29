__copyright__ = "Copyright (C) 2019  Red S"
__license__ = "GNU GPLv3"

import unittest
import re

from beancount_reds_plugins.capital_gains_classifier.gain_loss import gain_loss
from beancount.core import data
from beancount.parser import options
from beancount.parser import printer
from beancount import loader
from decimal import Decimal


# TODO: test with multiple cases
# "Income.*Capital-Gains:Short:.*: [":Short:", ":Short:Losses:", ":Short:Gains:"],
config = """{
     "Income.*:Capital-Gains.*" : [":Capital-Gains",  ":Capital-Gains:Gains",  ":Capital-Gains:Losses"],
   }"""


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


class TestLongShort(unittest.TestCase):

    def test_empty_entries(self):
        entries, _ = gain_loss([], options.OPTIONS_DEFAULTS.copy(), config)
        self.assertEqual([], entries)

    @loader.load_doc()
    def test_basic(self, entries, _, options_map):
        """
        2014-01-01 open Assets:Brokerage
        2014-01-01 open Assets:Bank
        2014-01-01 open Income:Capital-Gains

        2014-02-01 * "Buy"
          Assets:Brokerage    200 ORNG {1 USD}
          Assets:Bank        -200 USD

        2016-03-01 * "Sell"
          Assets:Brokerage   -100 ORNG {1 USD} @ 1.50 USD
          Assets:Bank         150 USD
          Income:Capital-Gains

        2016-03-02 * "Sell"
          Assets:Brokerage   -100 ORNG {1 USD} @ 0.50 USD
          Assets:Bank          50 USD
          Income:Capital-Gains

        """

        # # # Above should turn into:
        # 2016-03-01 * "Sell"
        #   Assets:Brokerage   -100 ORNG {1 USD} @ 1.50 USD
        #   Assets:Bank         150 USD
        #   Income:Capital-Gains:Gains -50 USD

        # 2016-03-02 * "Sell"
        #   Assets:Brokerage   -100 ORNG {1 USD} @ 0.50 USD
        #   Assets:Bank         150 USD
        #   Income:Capital-Gains:Losses 50 USD

        new_entries, _ = gain_loss(entries, options_map, config)
        self.assertEqual(8, len(new_entries))
        # for e in new_entries:
        #     print(printer.print_entry(e))
        # import pdb; pdb.set_trace()

        results = get_entries_with_narration(new_entries, "Sell")
        self.assertEqual('Income:Capital-Gains:Gains',  results[0].postings[2].account)
        self.assertEqual('Income:Capital-Gains:Losses', results[1].postings[2].account)
        self.assertEqual(Decimal("-50.00"), results[0].postings[2].units.number)
