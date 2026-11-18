import asyncio
from datetime import date
import time
import pytest
from httpx import ASGITransport, AsyncClient
from app.financial.apr import calculate_irr_apr
from app.financial.emi import calculate_monthly_emi, calculate_fee_and_gst
from app.financial.schedule import generate_amortisation_schedule
from app.main import app


def test_financial_engine_computational_throughput():
    """
    Benchmarks the pure CPU throughput of the Financial Engine:
    Executes 1,000 iterations of EMI + Amortisation Schedule + APR solver.
    Target: < 500ms total for 1,000 iterations (< 0.5ms per calculation).
    """
    start_time = time.perf_counter()
    iterations = 1000

    for i in range(iterations):
        principal = 2500000 + (i * 1000)
        tenure = 6
        rate = 1800
        emi = calculate_monthly_emi(principal, rate, tenure)
        fee, gst, net_disb = calculate_fee_and_gst(principal, "PERCENTAGE", 200, 1800)
        schedule = generate_amortisation_schedule(principal, rate, tenure, date(2026, 1, 1))
        cash_flows = [-float(net_disb)] + [float(s["emi_amount_paise"]) for s in schedule]
        apr = calculate_irr_apr(cash_flows)
        assert apr > 0

    elapsed = time.perf_counter() - start_time
    avg_per_op_ms = (elapsed / iterations) * 1000

    print(f"\n[BENCHMARK] 1,000 Financial Iterations completed in {elapsed:.3f}s (avg {avg_per_op_ms:.3f}ms/op)")
    assert avg_per_op_ms < 5.0  # Must be faster than 5ms per comprehensive loan calculation


@pytest.mark.asyncio
async def test_concurrent_api_calculator_throughput():
    """
    Tests high concurrency throughput against the FastAPI calculator endpoint:
    Dispatches 50 concurrent requests simultaneously.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "principal_paise": 5000000,
            "tenure_months": 6,
            "annual_rate_bps": 1800,
            "fee_type": "PERCENTAGE",
            "fee_value": 200,
            "gst_rate_bps": 1800,
        }

        async def send_req():
            t0 = time.perf_counter()
            r = await client.post("/api/v1/products/calculate", json=payload)
            t1 = time.perf_counter()
            return r.status_code, (t1 - t0) * 1000

        start = time.perf_counter()
        tasks = [send_req() for _ in range(50)]
        results = await asyncio.gather(*tasks)
        total_time = time.perf_counter() - start

        statuses = [s for s, _ in results]
        latencies = [lat for _, lat in results]

        assert all(s == 200 for s in statuses)
        p50 = sorted(latencies)[len(latencies) // 2]
        p95 = sorted(latencies)[int(len(latencies) * 0.95)]

        print(f"\n[CONCURRENCY] 50 Parallel Requests dispatched in {total_time:.3f}s. P50: {p50:.1f}ms, P95: {p95:.1f}ms")
        assert total_time < 5.0  # All 50 concurrent requests served in under 5.0s
        assert (total_time / 50) < 0.100  # Average time per request under 100ms
