import re
import unittest

import beancount_reds_plugins.zerosum.zerosum as zerosum

from beancount.core import data
from beancount.parser import options
from beancount import loader

config = """{
 'zerosum_accounts' : {
 'Assets:Zero-Sum-Accounts:Returns-and-Temporary'              : ('', 90),
 'Assets:Zero-Sum-Accounts:Checkings'                          : ('', 90),
 'Assets:Zero-Sum-Accounts:401k'                               : ('', 90),
  },
  'account_name_replace' : ('Zero-Sum-Accounts', 'ZSA-Matched'),
  'tolerance' : 0.0098,
 }"""


def get_entries_with_acc_regexp(entries, regexp):
    print(regexp)
    return [entry
            for entry in entries
            if (isinstance(entry, data.Transaction) and
                any(re.search(regexp, posting.account) for posting in entry.postings))]


class TestUnrealized(unittest.TestCase):

    def test_empty_entries(self):
        new_entries, _ = zerosum.zerosum([], options.OPTIONS_DEFAULTS.copy(), "{}")
        self.assertEqual([], new_entries)

    @loader.load_doc()
    def test_empty_config(self, entries, _, options_map):
        """
        2014-01-01 open Assets:Account1
        2014-01-01 open Assets:Account2
        2014-01-01 open Income:Misc

        2014-01-15 *
          Income:Misc           -1000 USD
          Assets:Account1

        2014-01-16 *
          Income:Misc           -1000 EUR
          Assets:Account2
        """
        new_entries, _ = zerosum.zerosum(entries, options_map, "{}")
        self.assertEqual(new_entries, entries)

    @loader.load_doc()
    def test_single_rename(self, entries, _, options_map):
        """
        2015-01-01 open Liabilities:Credit-Cards:Green
        2015-01-01 open Assets:Zero-Sum-Accounts:Returns-and-Temporary
        2015-06-15 * "Expensive furniture"
          Liabilities:Credit-Cards:Green  -2526.02 USD
          Assets:Zero-Sum-Accounts:Returns-and-Temporary             1263.01 USD
          Assets:Zero-Sum-Accounts:Returns-and-Temporary             1263.01 USD

        2015-06-23 * "Expensive furniture Refund"
          Liabilities:Credit-Cards:Green  1263.01 USD
          Assets:Zero-Sum-Accounts:Returns-and-Temporary

        2015-06-23 * "Expensive furniture Refund"
          Liabilities:Credit-Cards:Green  1263.01 USD
          Assets:Zero-Sum-Accounts:Returns-and-Temporary
        """
        new_entries, _ = zerosum.zerosum(entries, options_map, config)

        matched = get_entries_with_acc_regexp(new_entries, ':ZSA-Matched')
        self.assertEqual(3, len(matched))

        ref = [(0, 1), (0, 2), (1, 1), (2, 1)]

        for (m, p) in ref:
            self.assertEqual('Assets:ZSA-Matched:Returns-and-Temporary',
                             matched[m].postings[p].account)

    @loader.load_doc()
    def test_above_tolerance(self, entries, _, options_map):
        """
        2015-01-01 open Liabilities:Credit-Cards:Green
        2015-01-01 open Assets:Zero-Sum-Accounts:Returns-and-Temporary
        2015-06-15 * "Trinket"
          Liabilities:Credit-Cards:Green  -0.014 USD
          Assets:Zero-Sum-Accounts:Returns-and-Temporary

        2015-06-23 * "Trinket refund"
          Liabilities:Credit-Cards:Green  0.014 USD
          Assets:Zero-Sum-Accounts:Returns-and-Temporary
        """
        new_entries, _ = zerosum.zerosum(entries, options_map, config)

        matched = get_entries_with_acc_regexp(new_entries, ':ZSA-Matched')
        self.assertEqual(2, len(matched))

        ref = [(0, 1), (1, 1)]

        for (m, p) in ref:
            self.assertEqual('Assets:ZSA-Matched:Returns-and-Temporary', matched[m].postings[p].account)

    @loader.load_doc()
    def test_below_tolerance(self, entries, _, options_map):
        """
        2015-01-01 open Liabilities:Credit-Cards:Green
        2015-01-01 open Assets:Zero-Sum-Accounts:Returns-and-Temporary
        2015-06-15 * "Trinket"
          Liabilities:Credit-Cards:Green  -0.004 USD
          Assets:Zero-Sum-Accounts:Returns-and-Temporary

        2015-06-23 * "Trinket refund"
          Liabilities:Credit-Cards:Green  0.004 USD
          Assets:Zero-Sum-Accounts:Returns-and-Temporary
        """
        new_entries, _ = zerosum.zerosum(entries, options_map, config)

        matched = get_entries_with_acc_regexp(new_entries, ':ZSA-Matched')
        self.assertEqual(2, len(matched))

        ref = [(0, 1), (1, 1)]

        for (m, p) in ref:
            self.assertEqual('Assets:ZSA-Matched:Returns-and-Temporary', matched[m].postings[p].account)

    @loader.load_doc()
    def test_lookalike(self, entries, _, options_map):
        """
        2015-01-01 open Liabilities:Credit-Cards:Green
        2015-01-01 open Assets:Zero-Sum-Accounts:Returns-and-Temporary

        2020-06-01 * "Match two lookalike postings in one txn" ; should not error
          Assets:Zero-Sum-Accounts:Returns-and-Temporary  0.00 USD
          Assets:Zero-Sum-Accounts:Returns-and-Temporary  0.00 USD
        """
        new_entries, _ = zerosum.zerosum(entries, options_map, config)

        matched = get_entries_with_acc_regexp(new_entries, ':ZSA-Matched')
        self.assertEqual(1, len(matched))

        ref = [(0, 0), (0, 1)]

        for (m, p) in ref:
            self.assertEqual('Assets:ZSA-Matched:Returns-and-Temporary', matched[m].postings[p].account)

    @loader.load_doc()
    def test_both_postings_in_one_txn(self, entries, _, options_map):
        """
        2015-01-01 open Liabilities:Credit-Cards:Green
        2015-01-01 open Assets:Zero-Sum-Accounts:Returns-and-Temporary

        2020-01-01 * "Match both postings in one txn"
          Assets:Zero-Sum-Accounts:Returns-and-Temporary -1.00 USD
          Assets:Zero-Sum-Accounts:Returns-and-Temporary  1.00 USD
        """
        new_entries, _ = zerosum.zerosum(entries, options_map, config)

        matched = get_entries_with_acc_regexp(new_entries, ':ZSA-Matched')
        self.assertEqual(1, len(matched))

        ref = [(0, 0), (0, 1)]

        for (m, p) in ref:
            self.assertEqual('Assets:ZSA-Matched:Returns-and-Temporary', matched[m].postings[p].account)

    @loader.load_doc()
    def test_two_matched_below_tolerance(self, entries, _, options_map):
        """
        2015-01-01 open Liabilities:Credit-Cards:Green
        2015-01-01 open Assets:Zero-Sum-Accounts:Returns-and-Temporary

        2021-01-01 * "(two unmatched postings summing under tolerance)"
          Assets:Zero-Sum-Accounts:Returns-and-Temporary -0.001 USD
          Assets:Zero-Sum-Accounts:Returns-and-Temporary -0.002 USD
          Liabilities:Credit-Cards:Green
        """
        new_entries, _ = zerosum.zerosum(entries, options_map, config)

        matched_txns = get_entries_with_acc_regexp(new_entries, ':ZSA-Matched')
        self.assertEqual(1, len(matched_txns))
        matched_postings = sum(map(
            lambda posting: bool(re.search(':ZSA-Matched', posting.account)),
            matched_txns[0].postings))
        self.assertEqual(2, matched_postings)

    @loader.load_doc()
    def test_two_unmatched_above_tolerance(self, entries, _, options_map):
        """
        2015-01-01 open Liabilities:Credit-Cards:Green
        2015-01-01 open Assets:Zero-Sum-Accounts:Returns-and-Temporary

        2021-01-01 * "(two unmatched postings summing under tolerance)"
          Assets:Zero-Sum-Accounts:Returns-and-Temporary -0.00494 USD
          Assets:Zero-Sum-Accounts:Returns-and-Temporary -0.00496 USD
          Liabilities:Credit-Cards:Green
        """
        new_entries, _ = zerosum.zerosum(entries, options_map, config)

        matched_txns = get_entries_with_acc_regexp(new_entries, ':ZSA-Matched')
        self.assertEqual(0, len(matched_txns))

    @loader.load_doc()
    def test_no_match_id_by_default(self, entries, _, options_map):
        """
        2015-01-01 open Liabilities:Credit-Cards:Green
        2015-01-01 open Assets:Zero-Sum-Accounts:Returns-and-Temporary
        2015-06-15 * "Expensive furniture"
          Liabilities:Credit-Cards:Green  -2526.02 USD
          Assets:Zero-Sum-Accounts:Returns-and-Temporary             1263.01 USD
          Assets:Zero-Sum-Accounts:Returns-and-Temporary             1263.01 USD

        2015-06-23 * "Expensive furniture Refund"
          Liabilities:Credit-Cards:Green  1263.01 USD
          Assets:Zero-Sum-Accounts:Returns-and-Temporary
        """
        new_entries, _ = zerosum.zerosum(entries, options_map, config)

        matched = get_entries_with_acc_regexp(new_entries, ':ZSA-Matched')

        self.assertEqual(2, len(matched))
        for m in matched:
            for p in m.postings:
                self.assertTrue('match_id' not in p.meta)

    @loader.load_doc()
    def test_match_id_successfully_added(self, entries, _, options_map):
        """
        2023-01-01 open Income:Salary
        2023-01-01 open Assets:Bank:Checkings
        2023-01-01 open Assets:Zero-Sum-Accounts:Checkings
        2023-01-01 open Assets:Brokerage:401k
        2023-01-01 open Assets:Zero-Sum-Accounts:401k

        2024-02-15 * "Pay stub"
          Income:Salary                                -1100.06 USD
          Assets:Zero-Sum-Accounts:Checkings             999.47 USD
          Assets:Zero-Sum-Accounts:401k                  100.59 USD

        2024-02-16 * "Bank account"
          Assets:Bank:Checkings                          999.47 USD
          Assets:Zero-Sum-Accounts:Checkings

        2024-02-16 * "401k statement"
          Assets:Brokerage:401k                          100.59 USD
          Assets:Zero-Sum-Accounts:401k
        """
        new_entries, _ = zerosum.zerosum(
            entries, options_map,
            config[:-2] + """'match_metadata': True,\n}""")

        matched = dict(
            [(m.narration, m) for m in
             get_entries_with_acc_regexp(new_entries, ':ZSA-Matched')])

        self.assertEqual(3, len(matched))
        self.assertEqual(matched["Pay stub"].postings[1].meta['match_id'],
                         matched["Bank account"].postings[1].meta['match_id'])
        self.assertEqual(matched["Pay stub"].postings[2].meta['match_id'],
                         matched["401k statement"].postings[1].meta['match_id'])

    @loader.load_doc()
    def test_match_name_successfully_changed(self, entries, _, options_map):
        """
        2023-01-01 open Income:Salary
        2023-01-01 open Assets:Bank:Checkings
        2023-01-01 open Assets:Zero-Sum-Accounts:Checkings
        2023-01-01 open Assets:Brokerage:401k
        2023-01-01 open Assets:Zero-Sum-Accounts:401k

        2024-02-15 * "Pay stub"
          Income:Salary                                -1100.06 USD
          Assets:Zero-Sum-Accounts:Checkings             999.47 USD
          Assets:Zero-Sum-Accounts:401k                  100.59 USD

        2024-02-16 * "Bank account"
          Assets:Bank:Checkings                          999.47 USD
          Assets:Zero-Sum-Accounts:Checkings

        2024-02-16 * "401k statement"
          Assets:Brokerage:401k                          100.59 USD
          Assets:Zero-Sum-Accounts:401k
        """
        new_entries, _ = zerosum.zerosum(
            entries, options_map,
            config[:-2] + """'match_metadata': True,\n'match_metadata_name': 'MATCH'}""")

        matched = dict(
            [(m.narration, m) for m in
             get_entries_with_acc_regexp(new_entries, ':ZSA-Matched')])

        self.assertEqual(3, len(matched))
        self.assertEqual(matched["Pay stub"].postings[1].meta['MATCH'],
                         matched["Bank account"].postings[1].meta['MATCH'])
        self.assertEqual(matched["Pay stub"].postings[2].meta['MATCH'],
                         matched["401k statement"].postings[1].meta['MATCH'])

    @loader.load_doc()
    def test_no_links_by_default(self, entries, _, options_map):
        """
        2015-01-01 open Liabilities:Credit-Cards:Green
        2015-01-01 open Assets:Zero-Sum-Accounts:Returns-and-Temporary
        2015-06-15 * "Expensive furniture"
          Liabilities:Credit-Cards:Green  -2526.02 USD
          Assets:Zero-Sum-Accounts:Returns-and-Temporary             1263.01 USD
          Assets:Zero-Sum-Accounts:Returns-and-Temporary             1263.01 USD

        2015-06-23 * "Expensive furniture Refund"
          Liabilities:Credit-Cards:Green  1263.01 USD
          Assets:Zero-Sum-Accounts:Returns-and-Temporary
        """
        new_entries, _ = zerosum.zerosum(entries, options_map, config)

        matched = get_entries_with_acc_regexp(new_entries, ':ZSA-Matched')

        self.assertEqual(2, len(matched))
        for m in matched:
            self.assertFalse(any(link.startswith("ZeroSum.") for link in m.links))

    @loader.load_doc()
    def test_link_successfully_added(self, entries, _, options_map):
        """
        2023-01-01 open Income:Salary
        2023-01-01 open Assets:Bank:Checkings
        2023-01-01 open Assets:Zero-Sum-Accounts:Checkings
        2023-01-01 open Assets:Brokerage:401k
        2023-01-01 open Assets:Zero-Sum-Accounts:401k

        2024-02-15 * "Pay stub"
          Income:Salary                                -1100.06 USD
          Assets:Zero-Sum-Accounts:Checkings             999.47 USD
          Assets:Zero-Sum-Accounts:401k                  100.59 USD

        2024-02-16 * "Bank account"
          Assets:Bank:Checkings                          999.47 USD
          Assets:Zero-Sum-Accounts:Checkings

        2024-02-16 * "401k statement"
          Assets:Brokerage:401k                          100.59 USD
          Assets:Zero-Sum-Accounts:401k
        """
        new_entries, _ = zerosum.zerosum(
            entries, options_map,
            config[:-2] + """'link_transactions': True,\n}""")

        matched = dict(
            [(m.narration, m) for m in
             get_entries_with_acc_regexp(new_entries, ':ZSA-Matched')])

        self.assertEqual(3, len(matched))

        self.assertTrue(
            any(link.startswith("ZeroSum.") for link in (matched["Pay stub"].links & matched["Bank account"].links)))
        self.assertTrue(
            any(link.startswith("ZeroSum.") for link in (matched["Pay stub"].links & matched["401k statement"].links)))
        self.assertFalse(
            any(link.startswith("ZeroSum.") for link in (matched["Bank account"].links & matched["401k statement"].links)))

    @loader.load_doc()
    def test_link_prefix_successfully_changed(self, entries, _, options_map):
        """
        2023-01-01 open Income:Salary
        2023-01-01 open Assets:Bank:Checkings
        2023-01-01 open Assets:Zero-Sum-Accounts:Checkings
        2023-01-01 open Assets:Brokerage:401k
        2023-01-01 open Assets:Zero-Sum-Accounts:401k

        2024-02-15 * "Pay stub"
          Income:Salary                                -1100.06 USD
          Assets:Zero-Sum-Accounts:Checkings             999.47 USD
          Assets:Zero-Sum-Accounts:401k                  100.59 USD

        2024-02-16 * "Bank account"
          Assets:Bank:Checkings                          999.47 USD
          Assets:Zero-Sum-Accounts:Checkings

        2024-02-16 * "401k statement"
          Assets:Brokerage:401k                          100.59 USD
          Assets:Zero-Sum-Accounts:401k
        """
        new_entries, _ = zerosum.zerosum(
            entries, options_map,
            config[:-2] + """'link_transactions': True,\n'link_prefix': 'ZSM'}""")

        matched = dict(
            [(m.narration, m) for m in
             get_entries_with_acc_regexp(new_entries, ':ZSA-Matched')])

        self.assertEqual(3, len(matched))

        self.assertTrue(
            any(link.startswith("ZSM") for link in (matched["Pay stub"].links & matched["Bank account"].links)))
        self.assertTrue(
            any(link.startswith("ZSM") for link in (matched["Pay stub"].links & matched["401k statement"].links)))
        self.assertFalse(
            any(link.startswith("ZSM") for link in (matched["Bank account"].links & matched["401k statement"].links)))

    @loader.load_doc()
    def test_metadata_independent_from_linking(self, entries, _, options_map):
        """
        2023-01-01 open Income:Salary
        2023-01-01 open Assets:Bank:Checkings
        2023-01-01 open Assets:Zero-Sum-Accounts:Checkings
        2023-01-01 open Assets:Brokerage:401k
        2023-01-01 open Assets:Zero-Sum-Accounts:401k

        2024-02-15 * "Pay stub"
          Income:Salary                                -1100.06 USD
          Assets:Zero-Sum-Accounts:Checkings             999.47 USD
          Assets:Zero-Sum-Accounts:401k                  100.59 USD

        2024-02-16 * "Bank account"
          Assets:Bank:Checkings                          999.47 USD
          Assets:Zero-Sum-Accounts:Checkings

        2024-02-16 * "401k statement"
          Assets:Brokerage:401k                          100.59 USD
          Assets:Zero-Sum-Accounts:401k
        """
        new_entries, _ = zerosum.zerosum(
            entries, options_map,
            config[:-2] + """'match_metadata': True,\n'match_metadata_name': 'MATCH',\n
            'link_transactions': False,\n'link_prefix': 'ZSM'\n}""")

        matched = dict(
            [(m.narration, m) for m in
             get_entries_with_acc_regexp(new_entries, ':ZSA-Matched')])

        self.assertEqual(3, len(matched))
        self.assertEqual(matched["Pay stub"].postings[1].meta['MATCH'],
                         matched["Bank account"].postings[1].meta['MATCH'])
        self.assertEqual(matched["Pay stub"].postings[2].meta['MATCH'],
                         matched["401k statement"].postings[1].meta['MATCH'])

        for _, m in matched.items():
            self.assertFalse(any(link.startswith("ZSM") for link in m.links))

    @loader.load_doc()
    def test_linking_independent_from_metadata(self, entries, _, options_map):
        """
        2023-01-01 open Income:Salary
        2023-01-01 open Assets:Bank:Checkings
        2023-01-01 open Assets:Zero-Sum-Accounts:Checkings
        2023-01-01 open Assets:Brokerage:401k
        2023-01-01 open Assets:Zero-Sum-Accounts:401k

        2024-02-15 * "Pay stub"
          Income:Salary                                -1100.06 USD
          Assets:Zero-Sum-Accounts:Checkings             999.47 USD
          Assets:Zero-Sum-Accounts:401k                  100.59 USD

        2024-02-16 * "Bank account"
          Assets:Bank:Checkings                          999.47 USD
          Assets:Zero-Sum-Accounts:Checkings

        2024-02-16 * "401k statement"
          Assets:Brokerage:401k                          100.59 USD
          Assets:Zero-Sum-Accounts:401k
        """
        new_entries, _ = zerosum.zerosum(
            entries, options_map,
            config[:-2] + """'match_metadata': False,\n'match_metadata_name': 'MATCH',\n
            'link_transactions': True,\n'link_prefix': 'ZSM'\n}""")

        matched = dict(
            [(m.narration, m) for m in
             get_entries_with_acc_regexp(new_entries, ':ZSA-Matched')])

        self.assertEqual(3, len(matched))
        for _, m in matched.items():
            for p in m.postings:
                self.assertTrue('MATCH' not in p.meta)

        self.assertTrue(
            any(link.startswith("ZSM") for link in (matched["Pay stub"].links & matched["Bank account"].links)))
        self.assertTrue(
            any(link.startswith("ZSM") for link in (matched["Pay stub"].links & matched["401k statement"].links)))
        self.assertFalse(
            any(link.startswith("ZSM") for link in (matched["Bank account"].links & matched["401k statement"].links)))
