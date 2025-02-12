__copyright__ = "Copyright (C) 2019  Red S"
__license__ = "GNU GPLv3"

from beancount.parser import cmptest
from beancount_reds_plugins.capital_gains_classifier.gain_loss import gain_loss
from beancount.parser import options
# from beancount.parser import printer
from beancount import loader


# TODO: test with multiple cases
# "Income.*Capital-Gains:Short:.*: [":Short:", ":Short:Losses:", ":Short:Gains:"],
config = """{
     "Income.*:Capital-Gains.*" : [":Capital-Gains",  ":Capital-Gains:Gains",  ":Capital-Gains:Losses"],
   }"""


class TestGainLoss(cmptest.TestCase):

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

        new_entries, _ = gain_loss(entries, options_map, config)

        self.assertEqualEntries("""
        2014-01-01 open Assets:Brokerage
        2014-01-01 open Assets:Bank
        2014-01-01 open Income:Capital-Gains
        2014-01-01 open Income:Capital-Gains:Gains
        2014-01-01 open Income:Capital-Gains:Losses

        2014-02-01 * "Buy"
          Assets:Brokerage    200 ORNG {1 USD}
          Assets:Bank        -200 USD

        2016-03-01 * "Sell"
          Assets:Brokerage   -100 ORNG {1 USD, 2014-02-01} @ 1.50 USD
          Assets:Bank         150 USD
          Income:Capital-Gains:Gains -50 USD

        2016-03-02 * "Sell"
          Assets:Brokerage   -100 ORNG {1 USD, 2014-02-01} @ 0.50 USD
          Assets:Bank          50 USD
          Income:Capital-Gains:Losses 50 USD

        """, new_entries)
