import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert data["service"] == "LOANORBIT"
        assert data["is_sandbox_demo"] is True


@pytest.mark.asyncio
async def test_customer_otp_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Request OTP
        req_res = await client.post("/api/v1/auth/otp/request", json={"mobile_number": "+919876500001"})
        assert req_res.status_code == 200
        req_data = req_res.json()
        assert req_data["success"] is True

        # 2. Verify with wrong OTP
        bad_res = await client.post(
            "/api/v1/auth/otp/verify",
            json={"mobile_number": "+919876500001", "otp_code": "000000"}
        )
        assert bad_res.status_code == 401

        # 3. Verify with valid default OTP "123456"
        good_res = await client.post(
            "/api/v1/auth/otp/verify",
            json={"mobile_number": "+919876500001", "otp_code": "123456"}
        )
        assert good_res.status_code == 200
        tokens = good_res.json()
        assert "access_token" in tokens
        assert tokens["role"] == "CUSTOMER"


@pytest.mark.asyncio
async def test_admin_rbac_and_dashboard():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Superadmin login
        admin_res = await client.post(
            "/api/v1/auth/admin/login",
            json={"username": "superadmin", "password": "AdminPass123!"}
        )
        assert admin_res.status_code == 200
        admin_tokens = admin_res.json()
        super_token = admin_tokens["access_token"]

        # 2. Access dashboard metrics with superadmin token
        headers = {"Authorization": f"Bearer {super_token}"}
        dash_res = await client.get("/api/v1/admin/dashboard", headers=headers)
        assert dash_res.status_code == 200
        metrics = dash_res.json()
        assert metrics["total_customers"] >= 7
        assert metrics["active_loans"] >= 1

        # 3. Customer support admin attempts restricted ledger action
        support_res = await client.post(
            "/api/v1/auth/admin/login",
            json={"username": "support_lead", "password": "AdminPass123!"}
        )
        assert support_res.status_code == 200
        support_token = support_res.json()["access_token"]

        supp_headers = {"Authorization": f"Bearer {support_token}"}
        # Customer support role does NOT have LEDGER_VIEW or DISBURSEMENT_TRIGGER
        ledger_res = await client.get("/api/v1/ledger/accounts", headers=supp_headers)
        assert ledger_res.status_code == 403


@pytest.mark.asyncio
async def test_calculator_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "principal_paise": 2500000,
            "tenure_months": 6,
            "annual_rate_bps": 1800,
            "fee_type": "PERCENTAGE",
            "fee_value": 200,
            "gst_rate_bps": 1800,
        }
        res = await client.post("/api/v1/products/calculate", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["principal_paise"] == 2500000
        assert data["processing_fee_paise"] == 50000
        assert data["gst_paise"] == 9000
        assert data["net_disbursement_paise"] == 2441000
        assert len(data["schedule"]) == 6
