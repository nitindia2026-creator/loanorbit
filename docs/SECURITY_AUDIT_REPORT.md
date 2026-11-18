# LOANORBIT — SECURITY & RBAC AUDIT REPORT

**Date:** 2026-11-18  
**Security Lead:** Senior Security Engineer & Cloud Architect  
**Scope:** Authentication, Role-Based Access Control (RBAC), Token Rotation, IDOR Protection, Cryptographic Practices, and Sensitive Data Handling.  
**Result:** **100% PASS (All Security Scenarios Verified via Automated pytest Suite `backend/tests/test_security_rbac.py`)**

---

## 1. Role-Based Access Control (RBAC) Matrix

LOANORBIT implements granular least-privilege role-based access control across 6 administrator roles and customer accounts:

| Role | Permissions Assigned | Unauthorized Probes Rejected | Audit Status |
|:---|:---|:---|:---:|
| **SUPER_ADMIN** | All system permissions (Full Access) | None (Master Role) | **PASS** |
| **OPERATIONS_ADMIN** | Customer, KYC, Application, Product, Disbursement, Ledger View | User Management, Master Secrets | **PASS** |
| **KYC_OFFICER** | Customer Read, KYC Review, KYC Decide, Audit View | Disallow: Ledger, Disbursement, Underwriting | **PASS** |
| **UNDERWRITER** | Customer Read, Application Read, Application Decide | Disallow: KYC Decide, Disbursement, Ledger Post | **PASS** |
| **FINANCE_OFFICER** | Disbursement Trigger, Repayments, Ledger View & Post | Disallow: KYC Decide, Underwriting Decide | **PASS** |
| **CUSTOMER_SUPPORT** | Customer Read, Support Tickets Read & Respond | Disallow: Financial Ledger, Disbursement | **PASS** |
| **CUSTOMER** | Customer Read/Write (Self), Consents, Offers, Payments | Disallow: ALL Admin Endpoints | **PASS** |

### Verified RBAC Boundary Tests
- **KYC Officer** accessing General Ledger `/api/v1/ledger/accounts` $\rightarrow$ **HTTP 403 Forbidden**
- **KYC Officer** attempting Loan Disbursement `/api/v1/disbursements/trigger/{id}` $\rightarrow$ **HTTP 403 Forbidden**
- **Underwriter** attempting KYC Decision `/api/v1/admin/kyc/{id}/decision` $\rightarrow$ **HTTP 403 Forbidden**
- **Customer Support** attempting Ledger View `/api/v1/ledger/accounts` $\rightarrow$ **HTTP 403 Forbidden**
- **Customer** attempting Admin Dashboard `/api/v1/admin/dashboard` $\rightarrow$ **HTTP 401/403 Forbidden**

---

## 2. Authentication & Session Security

### Token Rotation and Expiration Policy
- **Access Tokens:** Short-lived JWTs (15 minutes), containing subject, role, issue time (`iat`), expiration (`exp`), and a cryptographically unique `jti` (JWT ID) claim to prevent replay attacks.
- **Refresh Tokens:** Long-lived (7 days) single-use tokens stored as SHA-256 hashes in the `refresh_tokens` table.
- **Single-Use Rotation:** Every call to `POST /api/v1/auth/refresh` immediately revokes the used refresh token and issues a new pair. Reusing an old refresh token is strictly rejected with HTTP 401.
- **Revocation on Logout:** `POST /api/v1/auth/logout` sets `revoked = True` on the token record, immediately terminating the session.

---

## 3. IDOR (Insecure Direct Object Reference) Protection

All customer-facing endpoints enforce ownership verification against the authenticated user ID (`current_user.id`):
- **Loan Inspection:** `GET /api/v1/loans/{id}` verifies `Loan.user_id == current_user.id`. Customer B cannot view Customer A's active loans $\rightarrow$ **HTTP 404/403**.
- **Document Isolation:** `GET /api/v1/documents/agreement/{loan_id}` and `/receipt/{payment_id}` reject unauthorized probes by foreign customers $\rightarrow$ **HTTP 404/403**.
- **Offer Protection:** Accepting an offer verifies `LoanOffer.application.user_id == current_user.id`.

---

## 4. Cryptographic Standards & Data Protection

- **Password Storage:** Argon2id hashing with Bcrypt fallback (`passlib.context.CryptContext`). Passwords are never stored in plaintext.
- **Masked Data:** Sensitive government ID numbers (PAN, Aadhaar) and bank account numbers are stored and transmitted in masked format (e.g. `XXXXXX1234F`).
- **Watermarked PDFs:** All server-generated documents (KFS, Sanction Letters, Loan Agreements, Receipts, NOCs) carry an indelible diagonal watermark: `LOANORBIT DEMO — NOT A REAL LOAN DOCUMENT`.
