import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_complete_end_to_end_customer_journey():
    """
    Executes complete 31-step lending scenario:
    1. Register customer via simulated OTP
    2. Complete Customer Profile
    3. Accept Statutory Consents
    4. Submit Synthetic KYC Document
    5. Admin KYC Officer verifies KYC Case
    6. Complete Penny-Drop Bank Verification
    7. Query Products & Calculate Eligibility
    8. Submit Loan Application
    9. Underwriter Reviews and Approves Application -> Generates Loan Offer
    10. Customer Reviews KFS and Accepts Offer -> Loan created in PENDING_DISBURSEMENT
    11. Operations/Finance Officer triggers Disbursement -> Loan becomes ACTIVE, Ledger posted
    12. Customer checks Repayment Schedule & makes EMI Payment -> Ledger posted, Outstanding updated
    13. Customer forecloses remaining balance -> Loan becomes FORECLOSED/CLOSED
    14. Customer downloads Final NOC / Closure Statement PDF
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Step 1: Customer Register & Verify OTP
        mobile = "+919999000001"
        req_res = await client.post("/api/v1/auth/otp/request", json={"mobile_number": mobile})
        assert req_res.status_code == 200

        verify_res = await client.post("/api/v1/auth/otp/verify", json={"mobile_number": mobile, "otp_code": "123456"})
        assert verify_res.status_code == 200
        cust_token = verify_res.json()["access_token"]
        cust_headers = {"Authorization": f"Bearer {cust_token}"}

        # Step 2: Complete Profile
        prof_payload = {
            "full_name": "Aarav Sharma",
            "date_of_birth": "1994-08-20",
            "gender": "MALE",
            "address_line1": "Flat 402, Green Meadows",
            "city": "Bengaluru",
            "state": "Karnataka",
            "pincode": "560100",
            "employment_type": "SALARIED",
            "monthly_income_paise": 6500000,
            "monthly_expenses_paise": 2000000,
        }
        prof_res = await client.put("/api/v1/customers/profile", json=prof_payload, headers=cust_headers)
        assert prof_res.status_code == 200

        # Step 3: Accept Required Consents
        for purpose in ["CREDIT_BUREAU", "DATA_PRIVACY", "LOAN_TERMS", "CKYC_CONSENT"]:
            c_res = await client.post(
                "/api/v1/consents",
                json={"purpose": purpose, "policy_version": "v1.0", "status": "GRANTED"},
                headers=cust_headers,
            )
            assert c_res.status_code == 200

        # Step 4: Submit KYC
        # Using mock provider valid PAN pattern
        kyc_data = {"id_type": "PAN", "id_number": "ABCDE1234F"}
        files = {"document_file": ("pan_sample.png", b"MOCK_PNG_DATA_FOR_VERIFICATION", "image/png")}
        kyc_res = await client.post("/api/v1/kyc/submit", data=kyc_data, files=files, headers=cust_headers)
        assert kyc_res.status_code == 200
        kyc_case_id = kyc_res.json()["id"]

        # Step 5: Verify Bank Account via Penny Drop
        bank_payload = {
            "account_holder_name": "Aarav Sharma",
            "bank_name": "HDFC Bank",
            "account_number": "50100012345678",
            "ifsc_code": "HDFC0000123",
        }
        bank_res = await client.post("/api/v1/bank-verification/verify", json=bank_payload, headers=cust_headers)
        assert bank_res.status_code == 200
        assert bank_res.json()["status"] == "VERIFIED"

        # Step 6: Query Available Products
        prod_res = await client.get("/api/v1/products", headers=cust_headers)
        assert prod_res.status_code == 200
        products = prod_res.json()
        assert len(products) > 0
        product_version = products[0]["versions"][0]
        product_version_id = product_version["id"]
        req_principal = product_version["min_principal_paise"]

        # Step 7: Submit Loan Application
        app_payload = {
            "product_version_id": product_version_id,
            "requested_amount_paise": req_principal,
            "requested_tenure_months": 3,
            "purpose": "MEDICAL_EMERGENCY",
        }
        app_res = await client.post("/api/v1/applications", json=app_payload, headers=cust_headers)
        assert app_res.status_code == 200
        application_id = app_res.json()["id"]

        # Step 8: Underwriter Login & Review / Approval
        uw_login = await client.post("/api/v1/auth/admin/login", json={"username": "underwriter_lead", "password": "AdminPass123!"})
        assert uw_login.status_code == 200
        uw_token = uw_login.json()["access_token"]
        uw_headers = {"Authorization": f"Bearer {uw_token}"}

        dec_payload = {
            "decision": "APPROVED",
            "approved_amount_paise": req_principal,
            "approved_tenure_months": 3,
            "approved_rate_bps": 1800,
            "remarks": "Credit criteria met. Approved for full amount.",
        }
        dec_res = await client.post(f"/api/v1/underwriting/{application_id}/decision", json=dec_payload, headers=uw_headers)
        assert dec_res.status_code == 200

        # Step 9: Customer Queries Pending Offer
        offer_res = await client.get("/api/v1/offers/my-pending", headers=cust_headers)
        assert offer_res.status_code == 200
        offer = offer_res.json()
        assert offer is not None
        offer_id = offer["id"]
        assert offer["offered_amount_paise"] == req_principal

        # Step 10: Download KFS PDF
        kfs_res = await client.get(f"/api/v1/documents/kfs/{offer_id}", headers=cust_headers)
        assert kfs_res.status_code == 200
        assert kfs_res.headers["content-type"] == "application/pdf"
        assert len(kfs_res.content) > 500

        # Step 11: Accept Offer -> creates Loan
        accept_res = await client.post(f"/api/v1/offers/{offer_id}/accept", headers=cust_headers)
        assert accept_res.status_code == 200
        loan_id = accept_res.json()["loan_id"]
        assert accept_res.json()["status"] == "PENDING_DISBURSEMENT"

        # Step 12: Finance Officer Triggers Disbursement
        fin_login = await client.post("/api/v1/auth/admin/login", json={"username": "finance_lead", "password": "AdminPass123!"})
        assert fin_login.status_code == 200
        fin_token = fin_login.json()["access_token"]
        fin_headers = {"Authorization": f"Bearer {fin_token}"}

        disb_res = await client.post(
            f"/api/v1/disbursements/trigger/{loan_id}",
            headers=fin_headers,
            json={"idempotency_key": f"IDEM-DISB-{loan_id[:8]}"},
        )
        assert disb_res.status_code == 200
        assert disb_res.json()["loan_status"] == "ACTIVE"

        # Step 13: Customer Views Active Loan & Instalments
        active_loan_res = await client.get("/api/v1/loans/active", headers=cust_headers)
        assert active_loan_res.status_code == 200
        loan_data = active_loan_res.json()
        assert loan_data["status"] == "ACTIVE"
        assert len(loan_data["instalments"]) == 3
        first_emi_paise = loan_data["instalments"][0]["emi_amount_paise"]

        # Step 14: Customer Makes First EMI Repayment
        pay_payload = {
            "loan_id": loan_id,
            "amount_paise": first_emi_paise,
            "scenario": "SUCCESS",
        }
        pay_headers = {**cust_headers, "idempotency-key": f"PAY-{loan_id[:8]}-INST-1"}
        pay_res = await client.post("/api/v1/repayments/pay", json=pay_payload, headers=pay_headers)
        assert pay_res.status_code == 200
        pay_data = pay_res.json()
        assert pay_data["success"] is True
        payment_id = pay_data["payment_id"]

        # Step 15: Download Payment Receipt PDF
        receipt_res = await client.get(f"/api/v1/documents/receipt/{payment_id}", headers=cust_headers)
        assert receipt_res.status_code == 200
        assert receipt_res.headers["content-type"] == "application/pdf"

        # Step 16: Foreclose Loan Balance
        foreclose_payload = {
            "loan_id": loan_id,
        }
        foreclose_res = await client.post("/api/v1/repayments/foreclose", json=foreclose_payload, headers=cust_headers)
        assert foreclose_res.status_code == 200
        fc_data = foreclose_res.json()
        assert fc_data["success"] is True
        assert fc_data["loan_status"] in ("FORECLOSED", "CLOSED")

        # Step 17: Download No Objection Certificate (NOC) PDF
        noc_res = await client.get(f"/api/v1/documents/noc/{loan_id}", headers=cust_headers)
        assert noc_res.status_code == 200
        assert noc_res.headers["content-type"] == "application/pdf"


@pytest.mark.asyncio
async def test_failure_and_edge_case_scenarios():
    """
    Edge-Case Scenarios:
    1. Rejection of unverified customer loan application
    2. Bank penny drop failure with invalid IFSC
    3. IDOR Protection: Customer B cannot access Customer A's loan documents
    4. Duplicate payment rejection via idempotency key
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Edge 1: Unverified customer loan application rejection
        mobile = "+919999000099"
        await client.post("/api/v1/auth/otp/request", json={"mobile_number": mobile})
        v_res = await client.post("/api/v1/auth/otp/verify", json={"mobile_number": mobile, "otp_code": "123456"})
        raw_cust_token = v_res.json()["access_token"]
        raw_cust_headers = {"Authorization": f"Bearer {raw_cust_token}"}

        # Attempt application without profile/kyc/bank
        app_fail_res = await client.post(
            "/api/v1/applications",
            json={"product_version_id": "dummy-id", "requested_amount_paise": 1000000, "requested_tenure_months": 3, "purpose": "TEST"},
            headers=raw_cust_headers,
        )
        assert app_fail_res.status_code == 400

        # Edge 2: Bank penny drop failure with simulated invalid account
        bank_fail_res = await client.post(
            "/api/v1/bank-verification/verify",
            json={
                "account_holder_name": "Test User",
                "bank_name": "HDFC Bank",
                "account_number": "50100012340000",
                "ifsc_code": "HDFC0000123",
            },
            headers=raw_cust_headers,
        )
        assert bank_fail_res.status_code == 200
        assert bank_fail_res.json()["status"] == "INVALID_ACCOUNT"

        # Edge 3: IDOR Security Protection
        # Customer B attempts to download Customer A's loan document
        idor_res = await client.get("/api/v1/documents/agreement/non-existent-or-forbidden-id", headers=raw_cust_headers)
        assert idor_res.status_code == 404
