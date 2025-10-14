import pytest
from datetime import date
from decimal import Decimal
from beancount.loader import load_string
from beancount_reds_plugins.box_accrual import box_accrual

def test_box_accrual_two_year_split():
    input_text = """
    2025-09-25 * "SPX 18DEC26" "Box Borrow 100k"
      synthetic_loan_expiry: 2026-12-18
      Assets:Investments:Taxable:IBKR-Original-1572:USD                        95,000 USD
      Expenses:Fees-and-Charges:Brokerage-Fees:Taxable:IBKR-Original-1572           6 USD
      Liabilities:Loans:BoxSpreadLoans                           -100,000 USD
      Income:Investments:Taxable:BoxTrades:Capital-Losses         -4994 USD
    """

    entries, _, options = load_string(input_text)

    # Apply the plugin directly
    new_entries, _ = box_accrual.box_accrual(entries, options, None)
    txn = [e for e in new_entries if e.__class__.__name__ == "Transaction"][0]

    # Extract Capital-Loss postings
    losses = [p for p in txn.postings if p.account.endswith(":Capital-Losses")]
    assert len(losses) == 2, "Should split into two loss postings"

    # Verify total matches exactly
    total_loss = sum(Decimal(p.units.number) for p in losses)
    assert total_loss == Decimal("-4994.00")

    # Verify amounts and effective_dates
    p2025, p2026 = losses
    assert p2025.meta["effective_date"] == date(2025, 12, 31)
    assert p2026.meta["effective_date"] == date(2026, 12, 18)

    # Rounded values
    assert p2025.units.number == Decimal("-1087.58")
    assert p2026.units.number == Decimal("-3906.42")

    # Optional: ensure no cost/price leaks
    for p in losses:
        assert p.cost is None
        assert p.price is None

