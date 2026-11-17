# LOANORBIT — Master Implementation Plan

**Project:** LOANORBIT  
**Tagline:** Your Credit Journey, Clearly Guided.  
**Execution Method:** Phase-by-phase strict architectural compliance with continuous verification.

---

## Phase Matrix

| Phase | Description | Deliverables | Verification Milestone |
| :--- | :--- | :--- | :--- |
| **Phase 0** | Repository Audit & Architecture Docs | 9 foundational doc specifications | Complete doc suite in `/docs` |
| **Phase 1** | Project Scaffolding & Infrastructure | `/backend`, `/admin`, `/mobile`, Docker Compose, Postgres, Redis | Health checks return HTTP 200 |
| **Phase 2** | Auth, RBAC & Customer Identity | JWT auth, OTP provider, Argon2id, Role permissions | Auth tests pass (tokens, RBAC matrix) |
| **Phase 3** | Consent, Mock KYC & Bank Verification | Consent tracking, doc upload, deterministic mock KYC & bank verification | KYC & Bank verification test suites pass |
| **Phase 4** | Loan Products, Eligibility & Calculator | Versioned products, rule-based eligibility, reducing balance EMI calculator | Financial accuracy tests pass |
| **Phase 5** | Application Lifecycle & Underwriting | Multi-step application, review, underwriting decisions, offer generation | State machine tests pass |
| **Phase 6** | Financial Engine & Double-Entry Ledger | Decimal EMI, paise integer accounting, balanced journal entries, allocation policy | Ledger zero-sum balance tests pass |
| **Phase 7** | Mock Lender, Disbursement & Repayments | Idempotent disbursement, UPI mock payment, reversals, webhook deduplication | Concurrency & idempotency tests pass |
| **Phase 8** | Customer Flutter App | Mobile app screens, Riverpod state, GoRouter navigation, Dio client | Flutter analysis & mobile tests pass |
| **Phase 9** | Admin React Dashboard | Vite + React + TS dashboard, TanStack Query, forms, charts, tables | Vite build & lint tests pass |
| **Phase 10** | Documents, Notifications & Support | Watermarked PDF generator (KFS, sanction letter), in-app notification & tickets | Document generation & ticket flows pass |
| **Phase 11** | Seed Data & Synthetic Scenarios | 7 synthetic customer scenarios, 6 admin roles, loan products | Idempotent seed script execution passes |
| **Phase 12** | Comprehensive QA & Security Audit | 16 end-to-end integration test scenarios, authorization & injection tests | 100% critical test suite passes |
| **Phase 13** | VPS Deployment & Acceptance Gate | Production compose configuration, backup/restore scripts, final reports | Deployment scripts & final acceptance gate |

---

## Phase Execution Details

### Phase 0: Audit & Architecture Documentation
- Create all 9 architecture specifications in `docs/`.
- Validate toolchain requirements and document environment limits.

### Phase 1: Scaffolding & Infrastructure
- Backend FastAPI skeleton with SQLAlchemy 2.0 async engine and Alembic migrations.
- Admin portal React 18+ Vite + TypeScript + Tailwind CSS scaffolding.
- Docker Compose defining `postgres`, `redis`, `backend`, `celery_worker`, `admin`, and `nginx`.
- Structured health check endpoint `/api/v1/health`.

### Phase 2: Auth, RBAC & Security
- Customer OTP-based synthetic authentication flow.
- Admin username/password authentication with Argon2id hashing.
- Dual-token (access + refresh) rotation and revocation logic.
- Role-Based Access Control (RBAC) with 6 pre-defined roles:
  1. `SUPER_ADMIN`
  2. `OPERATIONS_ADMIN`
  3. `KYC_OFFICER`
  4. `UNDERWRITER`
  5. `FINANCE_OFFICER`
  6. `CUSTOMER_SUPPORT`

### Phase 3: Consent, KYC & Bank Verification
- Consent engine storing consent ID, purpose, version, acceptance timestamp, device metadata.
- Document storage service for synthetic documents with magic byte and MIME validation.
- Mock KYC verification adapter with deterministic test cases (`APPROVED`, `REJECTED`, `MANUAL_REVIEW`).
- Mock Bank Account Verification with Penny-Drop simulation.

### Phase 4: Loan Products, Eligibility & Calculator
- Version-locked loan product catalog (e.g. Personal Starter Loan, Credit Builder, Salaried Express).
- Rule-based eligibility assessment evaluating income, expenses, FOIR (Fixed Obligation to Income Ratio).
- Reducing balance loan calculator with exact repayment schedule generation.

### Phase 5: Loan Applications & Underwriting
- 9-step loan application state machine (`DRAFT`, `SUBMITTED`, `UNDER_REVIEW`, `APPROVED`, `REJECTED`, `OFFER_GENERATED`, `ACCEPTED`, `DISBURSED`, `CLOSED`).
- Underwriter decision portal with mandatory remarks, audit trails, and policy versioning.
- Offer generation with expiry timestamps and sanction conditions.

### Phase 6: Financial Engine & Double-Entry Ledger
- Core formula: $EMI = P \times r \times \frac{(1+r)^n}{(1+r)^n - 1}$ computed with `Decimal`.
- Integer paise representation across database and ledger.
- Double-entry accounting system enforcing $\sum \text{Debits} == \sum \text{Credits}$ across all journal entries.
- Payment allocation waterfall: 1. Charges & Penalties $\rightarrow$ 2. Interest $\rightarrow$ 3. Principal.

### Phase 7: Mock Lender, Disbursement & Repayments
- Idempotent disbursement processor with mock lender adapter.
- Simulated UPI payment flow supporting Success, Failure, Pending, and Reversals.
- Ledger-backed compensating entries on payment reversal.

### Phase 8 & 9: Frontend Applications
- Flutter Customer Application: Responsive, modern mPokket-inspired UX with original LOANORBIT brand, Riverpod architecture, GoRouter navigation, dark/light themes.
- React Admin Portal: Data tables, KYC review workbench, Underwriting decision desk, Ledger explorer, Audit viewer.

### Phase 10 & 11: Documents, Notifications & Seed
- Server-side PDF generation with watermark: `"LOANORBIT DEMO — NOT A REAL LOAN DOCUMENT"`.
- Automated seeding of 7 customer personas representing every stage of the lending lifecycle.

### Phase 12 & 13: QA, Security & Deployment
- Automated test execution across backend, financial formulas, and frontend builds.
- Hostinger VPS Docker Compose setup and automated backup/restore scripts.
