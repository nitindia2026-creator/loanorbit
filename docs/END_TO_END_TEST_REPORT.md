# LOANORBIT — END-TO-END JOURNEY & EDGE-CASE VERIFICATION REPORT

**Date:** 2026-11-18  
**Verification Lead:** Principal Software Architect & QA Lead  
**Scope:** Complete Customer Journey, Underwriter & Operations Desk, Multi-Role Handshake, Double-Entry Posting, and Document Generation.  
**Result:** **100% PASS (All 31 Core Steps & Edge Cases Verified via Automated pytest Suite `backend/tests/test_e2e_journey.py`)**

---

## 1. 31-Step Synthetic Customer Journey Verification

| Step # | Journey Action | Endpoint / Subsystem | Verification Evidence | Status |
|:---:|:---|:---|:---|:---:|
| **1** | Register new customer | `POST /auth/otp/request` | OTP requested for synthetic mobile number `+919999000001` | **PASS** |
| **2** | Verify demo OTP | `POST /auth/otp/verify` | Sandbox OTP `123456` accepted; JWT access & refresh tokens issued | **PASS** |
| **3** | Complete Profile | `PUT /customers/profile` | Salaried persona profile created with monthly income and KYC details | **PASS** |
| **4** | Accept statutory consents | `POST /consents` | Granted `CREDIT_BUREAU`, `DATA_PRIVACY`, `LOAN_TERMS`, `CKYC_CONSENT` | **PASS** |
| **5** | Upload synthetic KYC docs | `POST /kyc/submit` | PAN document uploaded; file hash SHA256 recorded in secure vault | **PASS** |
| **6** | Mock KYC verification | `KYC Desk` | Synthetic PAN verified automatically; masked ID `XXXXXX1234F` | **PASS** |
| **7** | Bank account verification | `POST /bank-verification/verify` | Penny-drop simulated; IFSC validated; reference `PND-XXXX` issued | **PASS** |
| **8** | Calculate eligibility | `GET /products` | Products fetched; active version parameters resolved | **PASS** |
| **9** | View loan products | `GET /products` | Displayed min/max bounds, tenures, and APR disclosures | **PASS** |
| **10** | Calculate EMI & APR | `POST /products/calculate` | Exact reducing balance EMI and IRR-derived APR computed | **PASS** |
| **11** | Submit loan application | `POST /applications` | Application reference `APP-XXXX` generated; status `UNDER_REVIEW` | **PASS** |
| **12** | Log in as KYC officer | `POST /auth/admin/login` | Authorized as `kyc_lead` (Role: `KYC_OFFICER`) | **PASS** |
| **13** | Verify KYC case | `POST /kyc/cases/{id}/decision` | KYC case confirmed and marked `VERIFIED` | **PASS** |
| **14** | Log in as Underwriter | `POST /auth/admin/login` | Authorized as `underwriter_lead` (Role: `UNDERWRITER`) | **PASS** |
| **15** | Review application | `GET /underwriting/queue` | Credit policy checks evaluated | **PASS** |
| **16** | Approve application | `POST /underwriting/{id}/decision` | Application approved; decision logged with policy version | **PASS** |
| **17** | Generate loan offer | `POST /underwriting/{id}/decision` | Versioned offer created with KFS parameters; status `ISSUED` | **PASS** |
| **18** | Customer retrieves offer | `GET /offers/my-pending` | Offer reference `OFR-XXXX` retrieved with fee breakdowns | **PASS** |
| **19** | Review simulated KFS | `GET /documents/kfs/{offer_id}` | PDF dynamically rendered with required synthetic watermark | **PASS** |
| **20** | Accept offer | `POST /offers/{offer_id}/accept` | Application `OFFER_ACCEPTED`; Loan created in `PENDING_DISBURSEMENT` | **PASS** |
| **21** | Pre-generate schedule | `offers.py` Amortisation | Scheduled instalments created with reducing balance interest components | **PASS** |
| **22** | Trigger mock disbursement | `POST /disbursements/trigger/{id}` | Authorized as `finance_lead`; Net amount sent to verified bank | **PASS** |
| **23** | Verify active loan creation | `GET /loans/active` | Loan status updated to `ACTIVE`; disbursement timestamp recorded | **PASS** |
| **24** | Check repayment schedule | `GET /loans/active` | 3 monthly instalments scheduled with due dates | **PASS** |
| **25** | Make full simulated EMI | `POST /repayments/pay` | Mock UPI transaction processed with idempotency header | **PASS** |
| **26** | Verify transaction receipt | `GET /documents/receipt/{id}` | PDF receipt generated with allocated principal and interest lines | **PASS** |
| **27** | Verify payment allocation | `POST /repayments/pay` | Charges cleared first, then interest, then principal amortised | **PASS** |
| **28** | Verify ledger entries | General Ledger Engine | Journal Entry balanced: DR 1001 Cash, CR 1101 Principal, CR 4001 Interest | **PASS** |
| **29** | Verify outstanding balance | `GET /loans/active` | Principal balance decremented exactly by allocated principal amount | **PASS** |
| **30** | Foreclose remaining balance | `POST /repayments/foreclose` | Full remaining principal settled; status updated to `FORECLOSED` | **PASS** |
| **31** | Verify loan closure & NOC | `GET /documents/noc/{loan_id}` | NOC generated; outstanding balance Rs. 0.00 confirmed | **PASS** |

---

## 2. Failure and Edge-Case Scenarios Verified

| Edge-Case Scenario | Reproduction Vector | Expected Behaviour | Actual Behaviour | Status |
|:---|:---|:---|:---|:---:|
| **Premature Application Submission** | Customer submits loan without profile, verified KYC, or bank | HTTP 400 with specific business rule violation | HTTP 400 `BUSINESS_RULE_VIOLATION` returned | **PASS** |
| **Bank Penny Drop Failure** | Account ending in `0000` | Account flagged as `INVALID_ACCOUNT`; no verified bank record created | Status `INVALID_ACCOUNT` recorded; application blocked | **PASS** |
| **Invalid IFSC Regex Syntax** | Malformed IFSC code `INVALID_IFSC_99` | Pydantic regex pattern validation rejects input | HTTP 422 Unprocessable Entity returned | **PASS** |
| **IDOR Protection** | Customer B attempts to download Customer A's agreement/receipt | Resource authorization check checks `Loan.user_id == current_user.id` | HTTP 404 / 403 returned; documents isolated | **PASS** |
| **Disbursement Duplication Guard** | Triggering disbursement on an already `ACTIVE` loan | Idempotency or state check rejects second call | HTTP 400 `Loan is not awaiting disbursement` | **PASS** |

---

## 3. Summary

The end-to-end customer lending journey and administrative operations perform deterministically, reliably, and strictly within synthetic sandbox constraints. All financial operations maintain complete data consistency across database tables and general ledger accounts.
