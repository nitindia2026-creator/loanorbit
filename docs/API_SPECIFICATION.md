# LOANORBIT — REST API Specification (v1)

**Base URL:** `/api/v1`  
**Security:** Bearer Token (JWT), `X-Correlation-ID`, `Idempotency-Key` for mutative operations  

---

## 1. Authentication & Security Routes (`/auth`)

### 1.1 `POST /auth/otp/request`
Request a synthetic OTP for customer login/registration.
- **Request Body:**
  ```json
  {
    "mobile_number": "+919876543210"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "success": true,
    "message": "Simulated OTP dispatched",
    "delivery_channel": "MOCK_SMS",
    "expires_in_seconds": 300,
    "demo_hint": "Use test OTP: 123456"
  }
  ```

### 1.2 `POST /auth/otp/verify`
Verify simulated OTP and receive session tokens.
- **Request Body:**
  ```json
  {
    "mobile_number": "+919876543210",
    "otp_code": "123456"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "expires_in": 900,
    "user": {
      "id": "c7a8b0c1-23d4-4e5f-b678-901234567890",
      "mobile_number": "+919876543210",
      "is_onboarded": false
    }
  }
  ```

### 1.3 `POST /auth/admin/login`
Admin user authentication with username and password.
- **Request Body:**
  ```json
  {
    "username": "underwriter_lead",
    "password": "SecureDemoPassword123!"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "access_token": "eyJhbGci...",
    "refresh_token": "eyJhbGci...",
    "token_type": "bearer",
    "admin": {
      "id": "e987c6b5-a432-10fe-dcba-0987654321ba",
      "username": "underwriter_lead",
      "roles": ["UNDERWRITER"]
    }
  }
  ```

---

## 2. Customer Profile & Onboarding (`/customers`)

### 2.1 `GET /customers/me`
Retrieve active customer profile and workflow stage.

### 2.2 `PUT /customers/profile`
Create or update customer profile details (employment, income, address).

---

## 3. Consents & Verification (`/consents`, `/kyc`, `/bank-verification`)

### 3.1 `POST /consents`
Submit explicit consent acceptance.

### 3.2 `POST /kyc/submit`
Submit mock KYC document and identity details.
- **Request Body:** `multipart/form-data` with `document_file`, `id_type`, `id_number`.

### 3.3 `POST /bank-verification/verify`
Initiate simulated penny-drop bank verification.
- **Request Body:**
  ```json
  {
    "account_holder_name": "Arjun Sharma",
    "bank_name": "State Bank of India",
    "account_number": "100098765432",
    "ifsc_code": "SBIN0001234"
  }
  ```

---

## 4. Products & Calculator (`/products`, `/calculator`, `/eligibility`)

### 4.1 `GET /products`
List all active versioned loan products.

### 4.2 `POST /calculator/compute`
Compute exact reducing balance schedule, processing fees, GST, and net disbursement.
- **Request Body:**
  ```json
  {
    "product_id": "9a12bc34-56de-78fa-bcde-f12345678901",
    "principal_paise": 2500000,
    "tenure_months": 6
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "principal_paise": 2500000,
    "tenure_months": 6,
    "annual_interest_rate_percent": 18.0,
    "monthly_emi_paise": 438780,
    "total_interest_paise": 132680,
    "processing_fee_paise": 50000,
    "gst_on_fee_paise": 9000,
    "net_disbursement_paise": 2441000,
    "total_repayable_paise": 2632680,
    "apr_percent": 24.32,
    "schedule": [...]
  }
  ```

### 4.3 `GET /eligibility/check`
Run rule-based eligibility evaluation based on customer profile.

---

## 5. Application Lifecycle & Offers (`/applications`, `/offers`)

### 5.1 `POST /applications`
Submit a new loan application.

### 5.2 `GET /applications/{id}`
Retrieve application state, events, and linked offer if available.

### 5.3 `POST /offers/{id}/accept`
Accept sanction offer and trigger agreement execution.

### 5.4 `POST /offers/{id}/reject`
Explicitly decline loan offer.

---

## 6. Disbursements & Servicing (`/disbursements`, `/loans`, `/repayments`)

### 6.1 `POST /disbursements/trigger` (Admin / Automated)
Trigger mock disbursement for an accepted offer.
- **Header:** `Idempotency-Key`

### 6.2 `GET /loans/active`
Retrieve active loan details, next EMI, and repayment schedule.

### 6.3 `POST /repayments/pay`
Simulate UPI repayment.
- **Request Body:**
  ```json
  {
    "loan_id": "...",
    "amount_paise": 438780,
    "scenario": "SUCCESS"
  }
  ```

### 6.4 `POST /repayments/foreclose`
Generate payoff quotation and execute early settlement.

---

## 7. Admin, Underwriting & Ledger (`/admin/*`, `/ledger/*`)

- `GET /admin/dashboard`: Real-time aggregated financial and application metrics.
- `GET /admin/kyc/queue`: Pending KYC documents with preview URLs.
- `POST /admin/kyc/{id}/decision`: Verify or reject with mandatory remarks.
- `GET /admin/underwriting/queue`: Applications pending credit review.
- `POST /admin/underwriting/{id}/decision`: Approve, Reject, or Request Info.
- `GET /ledger/accounts`: Chart of accounts with live balances.
- `GET /ledger/journal-entries`: Balanced double-entry transactions log.
- `GET /admin/audit-logs`: Append-only security and operational audit trail.
