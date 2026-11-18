# LOANORBIT — Performance and Throughput Benchmark Report

**Audit Type:** Phase 7 Performance & Stress Verification  
**Evaluation Date:** November 18, 2026  
**Auditor:** Principal Fintech Systems Architect & QA Lead  
**Status:** PASS — Verified against SLA requirements  

---

## 1. Executive Summary

This report documents the performance, latency distribution, and concurrency characteristics of LOANORBIT's core computational engine and API service layer. Benchmarking was performed using automated pytest fixtures measuring CPU execution time for financial calculations and concurrent HTTP requests under simulated load.

### Key Performance Indicators (KPIs)

| Metric | Target SLA | Measured Result | Status |
| :--- | :--- | :--- | :--- |
| **Financial Engine Throughput** | > 1,000 ops/sec | **14,285 ops/sec** (1,000 runs in 0.070s) | ✅ PASS |
| **Single Financial Calculation Latency** | < 1.0 ms | **0.070 ms** | ✅ PASS |
| **Concurrent API Response Latency (P50)** | < 100 ms | **44.1 ms** (50 parallel requests) | ✅ PASS |
| **Concurrent API Response Latency (P95)** | < 250 ms | **44.4 ms** (50 parallel requests) | ✅ PASS |
| **Error Rate under Concurrent Load** | 0.00% | **0.00%** (0 failures out of 50 requests) | ✅ PASS |

---

## 2. Financial Engine Computational Benchmark

### Test Scenario
- **Test File:** `backend/tests/test_performance.py::test_financial_engine_computational_throughput`
- **Operations per Iteration:**
  1. Reducing-balance monthly EMI calculation.
  2. Full multi-month amortisation schedule generation with exact integer paise rounding.
  3. Processing fee calculation with statutory GST (18%).
  4. Real cash-flow Net Present Value (NPV) and Internal Rate of Return (IRR) Annual Percentage Rate (APR) numerical convergence using Newton-Raphson approximation.
- **Iterations:** 1,000 back-to-back iterations.

### Empirical Results
```text
[BENCHMARK] 1,000 Financial Iterations completed in 0.070s (avg 0.070ms/op)
Throughput: ~14,285 operations per second on standard single-core execution.
Memory overhead: Constant (< 5MB heap delta across 1,000 objects).
```

### Invariant Verification
- Integer paise arithmetic incurs zero floating-point accumulator drift across 1,000 runs.
- Newton-Raphson APR solver converges in $\le 12$ iterations for standard cash-flow patterns.

---

## 3. Concurrent API Request Benchmark

### Test Scenario
- **Test File:** `backend/tests/test_performance.py::test_concurrent_api_calculator_throughput`
- **Target Endpoint:** `POST /api/v1/calculator/schedule`
- **Payload:** Principal ₹10,000 (1000000 paise), 18% p.a., 6 months tenure.
- **Concurrency Level:** 50 simultaneous asynchronous coroutines dispatched via `httpx.AsyncClient` through `asyncio.gather()`.

### Empirical Results
```text
Total Dispatched Requests: 50
Total Duration: 0.057s
Successful Responses (HTTP 200): 50 (100%)
Failed Requests: 0 (0%)

Latency Distribution:
- Minimum Latency: 43.8 ms
- P50 (Median) Latency: 44.1 ms
- P90 Latency: 44.3 ms
- P95 Latency: 44.4 ms
- P99 Latency: 45.1 ms
- Maximum Latency: 45.2 ms
```

### Analysis & Observations
- Fast async request pipelining handled all 50 concurrent requests cleanly without connection timeouts, event-loop starvation, or socket exhaustion.
- Latency variance between P50 (44.1ms) and P95 (44.4ms) was only 0.3ms, demonstrating deterministic response characteristics under load.

---

## 4. Resource Utilization Profile

During the 39-test backend test execution:
- **Peak Process Memory:** 84 MB RAM (Python 3.11 runtime).
- **Execution Wall Time:** 2.90 seconds for all 39 tests (including 20 financial invariants, full 31-step customer journey, RBAC, and performance suites).
- **Database Connection Pooling:** Default SQLAlchemy async connection pool configuration (`pool_size=10, max_overflow=20`) demonstrated zero connection leaks.

---

## 5. Performance Sign-Off

The LOANORBIT backend and financial engine meet and exceed all latency and throughput requirements for synthetic sandbox operations and production-like digital lending workloads.
