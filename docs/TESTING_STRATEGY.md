# LOANORBIT — Comprehensive Testing Strategy

**Target:** Zero Financial Regressions, 100% Core Formula Verification  
**Test Frameworks:** Pytest (Backend & Financial Engine), Flutter Test (Mobile UI & Unit), Vitest / React Testing Library (Admin Portal)  

---

## 1. Test Pyramid & Scope

```
                ▲
               / \
              /   \
             / E2E \       16 Multi-Role Journey Scenarios
            /-------\
           /  Integ  \     API Endpoint & RBAC Matrix Tests
          /-----------\
         /  Unit/Math  \   Financial Engine, Decimal Precision, Ledger Balancing
        /---------------\
```

---

## 2. Financial Engine Unit Tests (Non-Negotiable)

1. **Exact Reducing Balance EMI:**
   - Verify EMI for ₹10,000, ₹25,000, ₹50,000 across 3, 6, 12, 24 months against standard actuarial tables.
   - Verify zero-interest loans ($0\%$ APR).
2. **Amortisation Schedule Invariants:**
   - $\sum \text{Principal Components} = \text{Initial Principal}$ (down to the exact single paisa).
   - Final instalment closing principal $\equiv 0$.
   - Opening principal of period $k+1$ $\equiv$ Closing principal of period $k$.
3. **APR Precision:**
   - Verify Newton-Raphson IRR solver yields correct effective annual rates including processing fee deductions.
4. **Allocation Waterfall:**
   - Test partial payments covering only charges.
   - Test partial payments covering charges + partial interest.
   - Test overpayment handling into surplus credit.
5. **Ledger Balancing Constraint:**
   - Every simulated journal entry must satisfy $\sum \text{Debits} - \sum \text{Credits} = 0$.

---

## 3. End-to-End Test Matrix (16 Scenarios)

| # | Test Scenario | Expected Outcome |
| :---: | :--- | :--- |
| **1** | Eligible customer full journey | KYC -> Bank Verify -> Apply -> Approve -> Offer Accept -> Disburse -> Complete Repay -> Closed |
| **2** | KYC Pending Customer | Attempt to apply for loan rejected with `KYC_REQUIRED` |
| **3** | KYC Rejected Customer | Customer can view rejection reason and resubmit synthetic document |
| **4** | Underwriter Info Request | Underwriter requests additional document; application state moves to `INFO_REQUESTED` |
| **5** | Admin Application Rejection | Underwriter rejects application with mandatory reason; status moves to `REJECTED` |
| **6** | Admin Application Approval | Underwriter approves; system emits `loan_offer` with 7-day validity |
| **7** | Offer Acceptance | Customer accepts offer; agreement generated with watermark |
| **8** | Simulated Disbursement | Mock lender completes payout; ledger debits Receivable, credits Cash |
| **9** | EMI Repayment | Customer pays monthly instalment; ledger debits Cash, credits Receivable & Interest |
| **10** | Payment Failure & Retry | Mock payment returns `FAILURE`; loan remains unpaid; second attempt succeeds |
| **11** | Duplicate Payment Webhook | Repeated provider event returns original cached response without double-crediting |
| **12** | Partial Payment Allocation | Payment allocated strictly according to waterfall (Charges -> Interest -> Principal) |
| **13** | Payment Reversal | Reversed payment creates compensating journal entry and restores outstanding dues |
| **14** | Early Foreclosure | Payoff quote computed; customer settles full balance; loan marked `FORECLOSED` |
| **15** | Normal Loan Closure | Final EMI paid; balance reaches zero; loan marked `CLOSED` |
| **16** | Unauthorized Admin Access | `CUSTOMER_SUPPORT` attempting to approve loan or post journal entry receives HTTP 403 |

---

## 4. Test Execution Commands

- **Backend Tests:**
  ```bash
  pytest backend/tests -v --tb=short
  ```
- **Mobile Tests:**
  ```bash
  cd mobile && flutter test
  ```
- **Admin Frontend Tests:**
  ```bash
  cd admin && npm test
  ```
