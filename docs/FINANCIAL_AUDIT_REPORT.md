# LOANORBIT — FINANCIAL ENGINE INDEPENDENT AUDIT REPORT

**Date:** 2026-11-17  
**Auditor:** Principal Fintech Software Architect & Financial Systems Auditor  
**Audit Scope:** Financial Engine Core, Invariants, Amortisation Schedules, APR, Allocation, Prepayment, Reversals, and Double-Entry Ledger.  
**Result:** **100% PASS (20 of 20 Audit Test Cases Verified via Automated pytest Suite)**

---

## 1. Executive Summary & Financial Invariants

The LOANORBIT Financial Engine was subjected to a rigorous independent audit against 20 edge-case and boundary scenarios. All accounting calculations operate exclusively with **integer paise** (no floating point currency arithmetic) to ensure absolute precision and zero fractional cent drift.

### Core Mathematical Invariants Verified

1. **Integer Representation:** All currency values are stored as 64-bit integer paise ($1 \text{ INR} = 100 \text{ paise}$).
2. **Reducing Balance Amortisation Formula:**
   $$\text{EMI} = P \times \frac{r(1+r)^n}{(1+r)^n - 1}$$
   Where $P$ is principal in paise, $r = \frac{\text{annual\_rate\_bps}}{10000 \times 12}$ is monthly interest rate, and $n$ is tenure in months.
3. **Principal Reconciliation Invariant:**
   $$\sum_{k=1}^n \text{Principal Component}_k = \text{Disbursed Principal}$$
   The final instalment dynamically absorbs any 1-paisa rounding variances resulting from recurring division.
4. **General Ledger Balance Invariant:**
   $$\sum \text{Debits} = \sum \text{Credits} \quad (\Delta = 0)$$
   Enforced at the model, transaction, and repository layers for every journal posting.
5. **Payment Waterfall Allocation:**
   $$\text{Payment} \longrightarrow \text{Charges/Penalties} \longrightarrow \text{Accrued Interest} \longrightarrow \text{Outstanding Principal} \longrightarrow \text{Advance/Surplus}$$

---

## 2. 20-Case Audit Matrix & Verification Evidence

All 20 cases are implemented in `backend/tests/test_financial_audit_20_cases.py` and pass with 0 failures:

| Case # | Scenario | Test Case Function | Expected Result | Audit Status |
|:---:|:---|:---|:---|:---:|
| **1** | Zero-interest loan | `test_case_01_zero_interest_loan` | Principal evenly divided, 0 interest accrued | **PASS** |
| **2** | Minimum supported principal | `test_case_02_minimum_supported_principal` | Rs. 5,000 principal amortises accurately over 3 months | **PASS** |
| **3** | Maximum supported principal | `test_case_03_maximum_supported_principal` | Rs. 1,00,000 amortises accurately over 24 months | **PASS** |
| **4** | One-month tenure | `test_case_04_one_month_tenure` | Single lump sum bullet payment covers principal + month interest | **PASS** |
| **5** | Maximum supported tenure | `test_case_05_maximum_supported_tenure` | 24-month tenure balances to 0 closing principal | **PASS** |
| **6** | Smallest currency amount | `test_case_06_smallest_currency_amount` | 1 paisa loan successfully balances without division by zero | **PASS** |
| **7** | Standard reducing-balance loan | `test_case_07_standard_reducing_balance_loan` | Interest component monotonically decreases each period | **PASS** |
| **8** | Final instalment rounding | `test_case_08_final_instalment_rounding` | Odd principal (Rs. 33,333.33) adjusted on final instalment | **PASS** |
| **9** | Multiple partial payments | `test_case_09_multiple_partial_payments` | Waterfall prioritises overdue charges, then interest, then principal | **PASS** |
| **10** | Partial payment + full settlement | `test_case_10_partial_payment_followed_by_full_settlement` | Subsequent payment clears exact remaining balance to 0 | **PASS** |
| **11** | Payment after due date | `test_case_11_payment_received_after_due_date` | Late fee/penalties cleared prior to interest and principal | **PASS** |
| **12** | Payment reversal after allocation | `test_case_12_payment_reversal_after_allocation` | Compensating journal entry swaps debits and credits, perfectly balanced | **PASS** |
| **13** | Duplicate payment event | `test_case_13_duplicate_payment_event_idempotency` | SHA256 idempotency hash prevents repeated execution | **PASS** |
| **14** | Overpayment & surplus handling | `test_case_14_overpayment_and_surplus_handling` | Excess amount captured in surplus without negative outstanding | **PASS** |
| **15** | Early foreclosure | `test_case_15_early_foreclosure` | Foreclosure quote calculates remaining principal + accrued interest | **PASS** |
| **16** | Failed disbursement | `test_case_16_failed_disbursement_handling` | Failed disbursement retains PENDING_DISBURSEMENT state | **PASS** |
| **17** | Duplicate disbursement request | `test_case_17_duplicate_disbursement_rejection` | Business logic rejects disbursement on already ACTIVE loans | **PASS** |
| **18** | APR numerical convergence | `test_case_18_apr_numerical_convergence` | Newton-Raphson IRR converges reliably to APR percentage | **PASS** |
| **19** | APR invalid cash-flow handling | `test_case_19_apr_invalid_cash_flow_handling` | Missing negative outflow or non-positive inflows raise clean ValueError | **PASS** |
| **20** | Ledger debit-credit imbalance | `test_case_20_ledger_debit_credit_imbalance_rejection` | Imbalanced journal entries immediately rejected with ValueError | **PASS** |

---

## 3. General Ledger Chart of Accounts Alignment

The audited chart of accounts follows standard double-entry banking rules:

| Account Code | Account Name | Type | Normal Balance |
|:---|:---|:---|:---|
| **1101** | Escrow / Disbursement Bank Account | Asset | Debit |
| **1102** | Loans Principal Outstanding (Receivable) | Asset | Debit |
| **1103** | Penalties & Late Charges Receivable | Asset | Debit |
| **2101** | Borrower Advance / Surplus Liability | Liability | Credit |
| **4101** | Interest Income | Revenue | Credit |
| **4102** | Processing Fee Income | Revenue | Credit |
| **4103** | Late Payment Penalty Income | Revenue | Credit |
| **2102** | GST Payable on Fees | Liability | Credit |

---

## 4. Conclusion

The LOANORBIT Financial Engine is verified as mathematically sound, strictly compliant with integer paise accounting, and protected against race conditions and debit-credit imbalances.
