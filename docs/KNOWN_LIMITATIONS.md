# LOANORBIT — Known Limitations & Sandbox Scope

**Purpose:** Transparent regulatory and operational boundary documentation.

---

## 1. Sandbox & Synthetic Restraints

1. **No Real Banking or UPI Rails:**
   - Real funds are never collected, debited, or disbursed.
   - All disbursement and repayment flows utilize deterministic mock providers (`MockLenderProvider`, `MockPaymentProvider`).
2. **Synthetic Identity Verification:**
   - No connection is made to UIDAI (Aadhaar), NSDL (PAN), or credit bureaus (CIBIL, Experian, Equifax).
   - Identity documents uploaded are synthetic placeholders and evaluated based on deterministic suffix rules (e.g. suffixes containing `FAIL` simulate rejection).
3. **Regulatory Disclaimer:**
   - LOANORBIT is an educational sandbox platform demonstrating digital lending architecture, actuarial accounting, and double-entry general ledger mechanics. It is not a licensed NBFC or bank.
   - All generated documents contain a mandatory watermark: `"LOANORBIT DEMO — NOT A REAL LOAN DOCUMENT"`.

---

## 2. Production Upgrades Required for Live Lending

If transitioning this sandbox to a licensed commercial NBFC/fintech in India:
1. **Lending Service Provider (LSP) Compliance:** Integration with RBI-registered NBFC partner APIs via mTLS.
2. **Account Aggregator (AA) Integration:** Connect to Sahamati / RBI-approved Account Aggregator ecosystem for bank statement consent pulls.
3. **Payment Gateway Integration:** Connect to NPCI eNACH/AutoPay and Razorpay/Cashfree payment gateways.
4. **Digital E-Sign:** Connect to Leegality or Digio for Aadhaar eSign (IT Act Section 10A compliant).
5. **Credit Bureau Pull:** Integrate CRIF High Mark or CIBIL TU REST APIs for credit score checks.
