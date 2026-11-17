# LOANORBIT — Security, RBAC & Data Protection

**Security Framework:** Zero-Trust Modular Architecture  
**Key Standards:** OWASP Top 10 API Security, Role-Based Access Control, Idempotency Protection  

---

## 1. Authentication & Session Security

1. **Password Hashing:**
   - Passwords for administrative accounts are hashed using **Argon2id** (memory cost = 65,536 KiB, iterations = 3, parallelism = 4) via `passlib[argon2]`. Plaintext passwords are never logged, echoed, or stored.
2. **JWT Dual-Token Model:**
   - **Access Token:** Short-lived (15 minutes), signed with asymmetric HMAC-SHA256 (`HS256`).
   - **Refresh Token:** Long-lived (7 days), stored hashed in PostgreSQL with single-use rotation semantics (refreshing revokes previous token).
3. **Session Revocation:**
   - Explicit logout instantly revokes the active refresh token family.

---

## 2. Role-Based Access Control (RBAC) Matrix

| Permission / Capability | SUPER_ADMIN | OPERATIONS_ADMIN | KYC_OFFICER | UNDERWRITER | FINANCE_OFFICER | CUSTOMER_SUPPORT |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| View System Dashboard | Yes | Yes | Limited | Limited | Financial | Support |
| Manage System Users & Roles | Yes | No | No | No | No | No |
| Create / Edit Loan Products | Yes | Yes | No | No | No | No |
| Review & Decide KYC Cases | Yes | Yes | Yes | No | No | View Only |
| Underwrite & Decide Loans | Yes | Yes | No | Yes | No | View Only |
| Trigger Loan Disbursements | Yes | Yes | No | No | Yes | No |
| Post Financial Adjustments | Yes | No | No | No | Yes | No |
| View General Ledger & Recon | Yes | Yes | No | No | Yes | No |
| Respond to Support Tickets | Yes | Yes | View Only | View Only | View Only | Yes |
| Export Financial Reports | Yes | Yes | No | No | Yes | No |

---

## 3. Data Protection & File Storage

1. **Storage Sandboxing:**
   - Customer KYC uploads and generated loan agreements are stored in `storage/private/`, located strictly outside web-server public document roots.
2. **File Validation:**
   - All uploaded files undergo strict size checks ($\le 5\text{MB}$), MIME-type verification, and magic byte signature checks (PNG, JPEG, PDF only).
3. **Authorized Document Access:**
   - Documents are accessed via short-lived, signed URLs or backend streaming endpoints verifying caller user ID or authorized staff roles.

---

## 4. Concurrency & Idempotency Controls

1. **Idempotency Keys:**
   - All financial mutations (`POST /disbursements`, `POST /repayments`, `POST /offers/{id}/accept`) require an `Idempotency-Key` header.
   - Idempotency records track initial request hash and cached response payload.
2. **Row-Level Locking:**
   - Multi-step ledger postings and loan status transitions utilize `SELECT ... FOR UPDATE` within atomic database transactions to eliminate race conditions and double-spending.

---

## 5. Audit Logging Architecture

Every state-changing API invocation writes an immutable record to `audit_logs`:
- `id` (UUID)
- `actor_type` (`CUSTOMER`, `ADMIN`, `SYSTEM`)
- `actor_id` (UUID)
- `action` (e.g. `KYC_APPROVED`, `LOAN_DISBURSED`, `OFFER_ACCEPTED`)
- `target_entity` (e.g. `loan_applications`)
- `target_id` (UUID)
- `ip_address` & `user_agent`
- `metadata` (JSONB)
- `created_at` (TIMESTAMPTZ UTC)

The audit log table has no `UPDATE` or `DELETE` triggers permitted in production.
