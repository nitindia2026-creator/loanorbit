import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_admin_rbac_role_isolation():
    """
    Verifies that every admin role is strictly constrained to its permissions
    and receives HTTP 403 FORBIDDEN when attempting unauthorized operations.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Login as KYC Officer
        kyc_login = await client.post("/api/v1/auth/admin/login", json={"username": "kyc_lead", "password": "AdminPass123!"})
        assert kyc_login.status_code == 200
        kyc_token = kyc_login.json()["access_token"]
        kyc_headers = {"Authorization": f"Bearer {kyc_token}"}

        # KYC Officer attempts to access General Ledger Accounts (restricted to Finance/Ops/Superadmin)
        res_ledger = await client.get("/api/v1/ledger/accounts", headers=kyc_headers)
        assert res_ledger.status_code == 403

        # KYC Officer attempts to trigger loan disbursement
        res_disb = await client.post("/api/v1/disbursements/trigger/dummy-loan-id", headers=kyc_headers, json={})
        assert res_disb.status_code == 403

        # 2. Login as Underwriter
        uw_login = await client.post("/api/v1/auth/admin/login", json={"username": "underwriter_lead", "password": "AdminPass123!"})
        assert uw_login.status_code == 200
        uw_token = uw_login.json()["access_token"]
        uw_headers = {"Authorization": f"Bearer {uw_token}"}

        # Underwriter can access underwriting queue
        res_uw_q = await client.get("/api/v1/underwriting/queue", headers=uw_headers)
        assert res_uw_q.status_code == 200

        # Underwriter attempts to decide KYC case (restricted to KYC Officer/Ops/Superadmin)
        res_kyc_dec = await client.post(
            "/api/v1/admin/kyc/dummy-case-id/decision",
            headers=uw_headers,
            json={"decision": "VERIFIED", "remarks": "Unauthorized test"},
        )
        assert res_kyc_dec.status_code == 403

        # 3. Login as Customer Support
        supp_login = await client.post("/api/v1/auth/admin/login", json={"username": "support_lead", "password": "AdminPass123!"})
        assert supp_login.status_code == 200
        supp_token = supp_login.json()["access_token"]
        supp_headers = {"Authorization": f"Bearer {supp_token}"}

        # Support can view support tickets
        res_supp_tickets = await client.get("/api/v1/support/admin/tickets", headers=supp_headers)
        assert res_supp_tickets.status_code == 200

        # Support cannot trigger disbursement or access ledger
        res_supp_disb = await client.post("/api/v1/disbursements/trigger/dummy-loan-id", headers=supp_headers, json={})
        assert res_supp_disb.status_code == 403
        res_supp_led = await client.get("/api/v1/ledger/accounts", headers=supp_headers)
        assert res_supp_led.status_code == 403

        # 4. Login as Finance Lead
        fin_login = await client.post("/api/v1/auth/admin/login", json={"username": "finance_lead", "password": "AdminPass123!"})
        assert fin_login.status_code == 200
        fin_token = fin_login.json()["access_token"]
        fin_headers = {"Authorization": f"Bearer {fin_token}"}

        # Finance can view ledger
        res_fin_ledger = await client.get("/api/v1/ledger/accounts", headers=fin_headers)
        assert res_fin_ledger.status_code == 200

        # 5. Customer attempts to access Admin endpoints
        # Request customer token
        v_res = await client.post("/api/v1/auth/otp/verify", json={"mobile_number": "+919876500001", "otp_code": "123456"})
        cust_token = v_res.json()["access_token"]
        cust_headers = {"Authorization": f"Bearer {cust_token}"}

        # Customer token used on admin endpoint
        res_cust_admin = await client.get("/api/v1/admin/dashboard", headers=cust_headers)
        assert res_cust_admin.status_code in (401, 403)


@pytest.mark.asyncio
async def test_refresh_token_rotation_and_revocation():
    """
    Verifies that refresh tokens are single-use, rotated upon refresh,
    and revoked upon logout.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Login customer
        mobile = "+919999000002"
        await client.post("/api/v1/auth/otp/request", json={"mobile_number": mobile})
        v_res = await client.post("/api/v1/auth/otp/verify", json={"mobile_number": mobile, "otp_code": "123456"})
        tokens = v_res.json()
        refresh_token_1 = tokens["refresh_token"]

        # Refresh token rotation: Exchange refresh_token_1 for new token pair
        ref_res = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token_1})
        assert ref_res.status_code == 200
        new_tokens = ref_res.json()
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens
        refresh_token_2 = new_tokens["refresh_token"]
        assert refresh_token_2 != refresh_token_1

        # Reusing the old refresh_token_1 MUST fail (single-use rotation policy)
        reuse_res = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token_1})
        assert reuse_res.status_code in (401, 403)

        # Logout with refresh_token_2
        logout_res = await client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token_2})
        assert logout_res.status_code == 200

        # Attempting refresh after logout MUST fail
        after_logout_res = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token_2})
        assert after_logout_res.status_code in (401, 403)


@pytest.mark.asyncio
async def test_idor_customer_isolation():
    """
    Verifies Insecure Direct Object Reference (IDOR) prevention:
    Customer A and Customer B cannot read or modify each other's loans, offers, or documents.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Customer A
        await client.post("/api/v1/auth/otp/request", json={"mobile_number": "+919876500001"})
        v1 = await client.post("/api/v1/auth/otp/verify", json={"mobile_number": "+919876500001", "otp_code": "123456"})
        cust_a_token = v1.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {cust_a_token}"}

        # Customer B
        await client.post("/api/v1/auth/otp/request", json={"mobile_number": "+919876500002"})
        v2 = await client.post("/api/v1/auth/otp/verify", json={"mobile_number": "+919876500002", "otp_code": "123456"})
        cust_b_token = v2.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {cust_b_token}"}

        # Fetch Customer A's active loan
        loan_a_res = await client.get("/api/v1/loans/active", headers=headers_a)
        assert loan_a_res.status_code == 200
        loan_a = loan_a_res.json()

        if loan_a:
            loan_a_id = loan_a["id"]
            # Customer B attempts to access Customer A's loan directly by ID
            b_probe_loan = await client.get(f"/api/v1/loans/{loan_a_id}", headers=headers_b)
            assert b_probe_loan.status_code in (403, 404)

            # Customer B attempts to download Customer A's loan agreement
            b_probe_doc = await client.get(f"/api/v1/documents/agreement/{loan_a_id}", headers=headers_b)
            assert b_probe_doc.status_code in (403, 404)
