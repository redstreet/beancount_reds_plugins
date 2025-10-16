# beancount-reds-plugins: Box Accrual

**Plugin:** `beancount_reds_plugins.box_accrual.box_accrual`  

**Purpose:** Automatically prorate synthetic loan (box spread) capital losses across
calendar years, creating accurate annual accrual entries for reporting.

---

## Why This Plugin Exists

When using synthetic loans (such as SPX box spreads) to borrow cash in a taxable
brokerage account, the total interest or loss from the trade typically spans multiple
calendar years.  Beancount records this as a single transaction with a total
`Capital-Losses` posting — but for proper **year-by-year tax accrual**, you need to
allocate the loss proportionally across years.

This plugin automates that.

---

## How It Works

- Detects transactions with metadata `synthetic_loan_expiry: YYYY-MM-DD`.
- Finds the single posting under an account ending in `:Capital-Losses`.
- Splits that posting into one per calendar year spanned by the loan period.
- Each split gets an `effective_date` metadata field (the last day of that year, or the
  expiry date for the final year).
- Loss amounts are **pro-rated by day count** and **rounded to cents**, preserving the
  total exactly.

## Example

### **Before (input)**

```beancount
2025-09-25 * "SPX 18DEC26" "Box Borrow 100k"
  synthetic_loan_expiry: 2026-12-18
  Assets:Investments:Taxable:IBKR-Original-1572:USD                        95,000 USD
  Expenses:Fees-and-Charges:Brokerage-Fees:Taxable:IBKR-Original-1572           6 USD
  Liabilities:Loans:BoxSpreadLoans                           -100,000 USD
  Income:Investments:Taxable:BoxTrades:Capital-Losses          -4994 USD
````

### **After (output)**

```beancount
2025-09-25 * "SPX 18DEC26" "Box Borrow 100k"
  synthetic_loan_expiry: 2026-12-18
  Assets:Investments:Taxable:IBKR-Original-1572:USD                        95,000 USD
  Expenses:Fees-and-Charges:Brokerage-Fees:Taxable:IBKR-Original-1572           6 USD
  Liabilities:Loans:BoxSpreadLoans                           -100,000 USD
  Income:Investments:Taxable:BoxTrades:Capital-Losses         -1087.58 USD
    effective_date: 2025-12-31
  Income:Investments:Taxable:BoxTrades:Capital-Losses         -3906.42 USD
    effective_date: 2026-12-18
```

Total loss still equals −4994 USD, but now the loss is distributed across years for accurate year-end accrual reporting.

---

## Usage

Add this line to your main `.beancount` file:

```beancount
plugin "beancount_reds_plugins.box_accrual.box_accrual"
plugin "beancount_reds_plugins.effective_date.effective_date"
```

> ⚠️ **Important:**
> This plugin requires the `effective_date` plugin to be loaded *after* it,
> since it relies on `effective_date` to shift postings into the correct reporting periods.
