"""TODO"""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from beancount.core import data, amount

PLUGIN_NAME = "beancount_reds_plugins.box_accrual.box_accrual"
__plugins__ = ("box_accrual",)


def _as_date(val):
    if isinstance(val, date):
        return val
    if isinstance(val, str):
        return date.fromisoformat(val)
    return None


def box_accrual(entries, unused_options_map, config):
    out = []
    for entry in entries:
        if not isinstance(entry, data.Transaction):
            out.append(entry)
            continue

        expiry_raw = entry.meta.get("synthetic_loan_expiry")
        expiry_date = _as_date(expiry_raw)
        if not expiry_date:
            out.append(entry)
            continue

        # Find the single Capital-Losses posting
        losses = [p for p in entry.postings if p.account.endswith(":Capital-Losses")]
        if len(losses) != 1:
            out.append(entry)
            continue

        loss_p = losses[0]
        total_loss = Decimal(loss_p.units.number)
        ccy = loss_p.units.currency
        start = entry.date

        if start.year == expiry_date.year:
            out.append(entry)
            continue

        # Inclusive day count
        total_days = (expiry_date - start).days + 1
        if total_days <= 0:
            out.append(entry)
            continue

        # Build year splits
        fractions = []
        for year in range(start.year, expiry_date.year + 1):
            seg_start = max(start, date(year, 1, 1))
            seg_end = min(expiry_date, date(year, 12, 31))
            seg_days = (seg_end - seg_start).days + 1
            if seg_days <= 0:
                continue
            fractions.append((year, seg_days, seg_end))

        # Calculate and round each year's loss
        splits = []
        rounded_sum = Decimal("0.00")
        for i, (year, seg_days, seg_end) in enumerate(fractions):
            frac = Decimal(seg_days) / Decimal(total_days)
            seg_amt = total_loss * frac
            if i < len(fractions) - 1:
                seg_amt = seg_amt.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                rounded_sum += seg_amt
            else:
                # Final segment = whatever remainder keeps totals exact
                seg_amt = total_loss - rounded_sum
                seg_amt = seg_amt.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            splits.append(
                data.Posting(
                    account=loss_p.account,
                    units=amount.Amount(seg_amt, ccy),
                    cost=None,
                    price=None,
                    flag=None,
                    meta={"effective_date": seg_end},
                )
            )

        new_postings = [p for p in entry.postings if p is not loss_p] + splits
        out.append(entry._replace(postings=new_postings))

    return out, []

