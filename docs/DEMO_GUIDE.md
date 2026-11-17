# LOANORBIT — Synthetic Demo & Presentation Guide

**Sandbox Notice:** Every transaction, customer profile, offer, and agreement in this system is strictly synthetic. No real funds, bureaus, or banking rails are connected.

---

## 1. Quick Credentials Reference

### Admin Portal Credentials (`/admin` or `http://localhost:3000`)

| Role | Username | Password | Accessible Capabilities |
| :--- | :--- | :--- | :--- |
| **Super Admin** | `superadmin` | `AdminPass123!` | Complete access to all desks, users, and ledger |
| **Credit Underwriter** | `underwriter_lead` | `AdminPass123!` | Credit review queue, underwrite applications, issue offers |
| **KYC Officer** | `kyc_lead` | `AdminPass123!` | Review pending identity documents, approve or reject |
| **Finance Officer** | `finance_lead` | `AdminPass123!` | Trigger disbursements, view general ledger & reconciliation |
| **Operations Manager** | `ops_lead` | `AdminPass123!` | Customer profiles, applications, and general monitoring |
| **Customer Support** | `support_lead` | `AdminPass123!` | Support tickets, customer lookup (Restricted from ledger) |

---

### Customer Mobile Application Personas

| Persona ID | Demo Mobile Number | Default Test OTP | Profile State & Current Loan |
| :--- | :--- | :--- | :--- |
| **Customer 01** | `+919800000001` | `123456` | Eligible, KYC Verified, Bank Verified, Ready to Apply |
| **Customer 02** | `+919800000002` | `123456` | KYC Pending Verification (Awaiting KYC Officer) |
| **Customer 03** | `+919800000003` | `123456` | KYC Rejected Persona (Demonstrates Resubmission flow) |
| **Customer 04** | `+919800000004` | `123456` | Loan Application Under Review at Credit Desk |
| **Customer 05** | `+919800000005` | `123456` | Active Loan Disbursed, Repaying EMIs |
| **Customer 06** | `+919800000006` | `123456` | Overdue Loan Account (Demonstrates collections/charges) |
| **Customer 07** | `+919800000007` | `123456` | Fully Closed & Settled Loan Account |

---

## 2. End-to-End Walkthrough Scenarios

### Scenario A: New Customer Loan Application Journey
1. Open Flutter Mobile App (or run `flutter run` in `mobile/`).
2. Log in with **Customer 01** (`+919800000001`, OTP: `123456`).
3. On the **Calculator** tab, drag the principal slider to ₹25,000 and select **6 Months**.
4. Observe real-time dynamic backend calculations: Monthly EMI (approx ₹4,388), 2% processing fee, 18% GST on fee, Net disbursement estimate, and effective APR.
5. Tap **Proceed to Loan Application**.
6. Review the 3 verified prerequisites (Profile, KYC, Bank Account) and consent statement.
7. Tap **Submit Application for Review**.
8. Notice application moves to `UNDER_REVIEW` with an assigned reference (e.g. `APP-XXXXXX`).

### Scenario B: Underwriting & Offer Issuance (Admin Desk)
1. Open Admin Portal in browser at `http://localhost:3000` (or `http://localhost/admin/`).
2. Log in as `underwriter_lead` (`AdminPass123!`).
3. Navigate to **Underwriting** from the sidebar.
4. Locate the newly submitted application in the queue.
5. Tap **Underwrite** to open the credit decision dialog.
6. Enter credit assessment remarks and click **Approve & Issue Offer**.
7. The backend calculates actuarial repayment schedules, sets a 7-day expiry, and transitions application status to `APPROVED` / `OFFER_GENERATED`.

### Scenario C: Customer Offer Acceptance & Simulated Disbursement
1. As the customer, accept the offer.
2. In the Admin Portal, log in as `finance_lead`.
3. Open **General Ledger** $\rightarrow$ Observe that triggering disbursement debits Loan Principal Receivable (`1101`) and credits Cash Pool (`1001`), Processing Fee Revenue (`4002`), and GST Payable (`2101`) in exact balanced sums down to integer paise.
4. Loan status moves to `ACTIVE`.

### Scenario D: Instant Simulated UPI Repayment & Ledger Posting
1. In the customer mobile app, switch to the **Loans & EMI** tab.
2. View the active loan card, outstanding principal, and upcoming instalment schedule.
3. Tap **Simulate Instant UPI Repayment**.
4. Select **Pay Full EMI** (or **Partial Payment**).
5. Watch the loan balance update immediately, the instalment status transition to `PAID`, and balanced journal lines post to the General Ledger.
