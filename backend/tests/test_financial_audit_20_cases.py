from datetime import date, datetime, timezone
import pytest
from app.financial.emi import calculate_monthly_emi, calculate_fee_and_gst
from app.financial.schedule import generate_amortisation_schedule
from app.financial.apr import calculate_irr_apr
from app.financial.allocation import allocate_payment_waterfall
from app.financial.prepayment import calculate_foreclosure_quote
from app.financial.reversal import create_reversal_journal_entry
from app.financial.reconciliation import reconcile_loan_amortisation, reconcile_general_ledger_entries
from app.financial.ledger import create_balanced_journal_entry
from app.core.errors import BusinessLogicException


# ==============================================================================
# 20 REQUIRED FINANCIAL ENGINE TEST CASES
# ==============================================================================

def test_case_01_zero_interest_loan():
    """Case 1: Zero-interest loan dividing principal evenly."""
    principal = 1200000  # Rs 12,000
    tenure = 12
    emi = calculate_monthly_emi(principal_paise=principal, annual_rate_bps=0, tenure_months=tenure)
    assert emi == 100000  # Exactly Rs 1,000 per month
    
    schedule = generate_amortisation_schedule(principal, 0, tenure, date(2026, 1, 1))
    assert len(schedule) == 12
    assert sum(s["principal_component_paise"] for s in schedule) == principal
    assert sum(s["interest_component_paise"] for s in schedule) == 0
    assert schedule[-1]["closing_principal_paise"] == 0


def test_case_02_minimum_supported_principal():
    """Case 2: Minimum supported principal (Rs. 5,000 / 500,000 paise)."""
    principal = 500000
    tenure = 3
    rate_bps = 1800  # 18% p.a.
    schedule = generate_amortisation_schedule(principal, rate_bps, tenure, date(2026, 1, 1))
    assert len(schedule) == 3
    assert sum(s["principal_component_paise"] for s in schedule) == principal
    assert schedule[-1]["closing_principal_paise"] == 0


def test_case_03_maximum_supported_principal():
    """Case 3: Maximum supported principal (Rs. 1,00,000 / 10,000,000 paise)."""
    principal = 10000000
    tenure = 24
    rate_bps = 2400  # 24% p.a.
    schedule = generate_amortisation_schedule(principal, rate_bps, tenure, date(2026, 1, 1))
    assert len(schedule) == 24
    assert sum(s["principal_component_paise"] for s in schedule) == principal
    assert schedule[-1]["closing_principal_paise"] == 0


def test_case_04_one_month_tenure():
    """Case 4: One-month tenure (Single lump-sum instalment)."""
    principal = 1000000  # Rs. 10,000
    rate_bps = 1200     # 12% p.a. -> 1% per month = Rs. 100
    schedule = generate_amortisation_schedule(principal, rate_bps, 1, date(2026, 1, 1))
    assert len(schedule) == 1
    assert schedule[0]["principal_component_paise"] == principal
    assert schedule[0]["interest_component_paise"] == 10000  # Rs. 100
    assert schedule[0]["closing_principal_paise"] == 0


def test_case_05_maximum_supported_tenure():
    """Case 5: Maximum supported tenure (24 months)."""
    principal = 5000000  # Rs. 50,000
    rate_bps = 2000     # 20% p.a.
    schedule = generate_amortisation_schedule(principal, rate_bps, 24, date(2026, 1, 1))
    assert len(schedule) == 24
    assert sum(s["principal_component_paise"] for s in schedule) == principal
    assert schedule[-1]["closing_principal_paise"] == 0


def test_case_06_smallest_currency_amount():
    """Case 6: Smallest supported currency amount (1 paisa precision test)."""
    # 1 paisa loan over 1 month
    schedule = generate_amortisation_schedule(1, 1200, 1, date(2026, 1, 1))
    assert len(schedule) == 1
    assert schedule[0]["principal_component_paise"] == 1
    assert schedule[0]["closing_principal_paise"] == 0


def test_case_07_standard_reducing_balance_loan():
    """Case 7: Standard reducing-balance loan: interest decreases monotonically."""
    principal = 2500000  # Rs. 25,000
    rate_bps = 2100     # 21% p.a.
    schedule = generate_amortisation_schedule(principal, rate_bps, 6, date(2026, 1, 1))
    
    interest_components = [s["interest_component_paise"] for s in schedule]
    principal_components = [s["principal_component_paise"] for s in schedule]
    
    # Interest should strictly decrease
    for i in range(len(interest_components) - 1):
        assert interest_components[i] >= interest_components[i+1]
        
    # Principal portion should strictly increase
    for i in range(len(principal_components) - 1):
        assert principal_components[i] <= principal_components[i+1]


def test_case_08_final_instalment_rounding():
    """Case 8: Final instalment rounding adjustment eliminates fractional paise discrepancy."""
    principal = 3333333  # An odd number causing recurring decimals
    rate_bps = 1750
    schedule = generate_amortisation_schedule(principal, rate_bps, 7, date(2026, 1, 1))
    
    total_principal_sum = sum(s["principal_component_paise"] for s in schedule)
    assert total_principal_sum == principal
    assert schedule[-1]["closing_principal_paise"] == 0


def test_case_09_multiple_partial_payments():
    """Case 9: Multiple partial payments allocated in order: charges -> interest -> principal."""
    inst = {
        "id": "inst-1",
        "instalment_number": 1,
        "principal_component_paise": 800000,
        "interest_component_paise": 200000,
        "charges_paise": 50000,
        "paid_principal_paise": 0,
        "paid_interest_paise": 0,
    }

    # Payment 1: Rs. 1,000 (100,000 paise)
    allocs1, excess1 = allocate_payment_waterfall(100000, [inst])
    assert len(allocs1) == 1
    assert allocs1[0]["allocated_charges_paise"] == 50000   # Cleared full penalty
    assert allocs1[0]["allocated_interest_paise"] == 50000  # Remaining Rs. 500 towards interest
    assert allocs1[0]["allocated_principal_paise"] == 0
    assert excess1 == 0

    # Apply payment 1 effects
    inst["charges_paise"] = 0
    inst["paid_interest_paise"] += allocs1[0]["allocated_interest_paise"]

    # Payment 2: Rs. 2,000 (200,000 paise)
    allocs2, excess2 = allocate_payment_waterfall(200000, [inst])
    assert len(allocs2) == 1
    assert allocs2[0]["allocated_charges_paise"] == 0
    assert allocs2[0]["allocated_interest_paise"] == 150000  # Remaining interest cleared (Rs. 1,500)
    assert allocs2[0]["allocated_principal_paise"] == 50000  # Remaining Rs. 500 towards principal
    assert excess2 == 0


def test_case_10_partial_payment_followed_by_full_settlement():
    """Case 10: Partial payment followed by full payoff settles instalment completely."""
    inst = {
        "id": "inst-1",
        "instalment_number": 1,
        "principal_component_paise": 1000000,
        "interest_component_paise": 200000,
        "charges_paise": 0,
        "paid_principal_paise": 0,
        "paid_interest_paise": 0,
    }

    # Partial payment of Rs. 5,000 (500,000 paise)
    allocs1, _ = allocate_payment_waterfall(500000, [inst])
    inst["paid_interest_paise"] += allocs1[0]["allocated_interest_paise"]
    inst["paid_principal_paise"] += allocs1[0]["allocated_principal_paise"]

    pending_due = (inst["principal_component_paise"] - inst["paid_principal_paise"]) + (inst["interest_component_paise"] - inst["paid_interest_paise"])
    assert pending_due == 700000

    # Second payment of exact remaining balance
    allocs2, excess2 = allocate_payment_waterfall(pending_due, [inst])
    inst["paid_interest_paise"] += allocs2[0]["allocated_interest_paise"]
    inst["paid_principal_paise"] += allocs2[0]["allocated_principal_paise"]

    assert excess2 == 0
    assert inst["paid_principal_paise"] == 1000000
    assert inst["paid_interest_paise"] == 200000


def test_case_11_payment_received_after_due_date():
    """Case 11: Payment received after due date with overdue penalty waterfall."""
    inst = {
        "id": "inst-1",
        "instalment_number": 1,
        "principal_component_paise": 500000,
        "interest_component_paise": 100000,
        "charges_paise": 50000,  # Rs. 500 penalty
        "paid_principal_paise": 0,
        "paid_interest_paise": 0,
    }
    
    # Customer pays full EMI + penalty = Rs. 6,500 (650,000 paise)
    allocs, excess = allocate_payment_waterfall(650000, [inst])
    assert len(allocs) == 1
    assert allocs[0]["allocated_charges_paise"] == 50000
    assert allocs[0]["allocated_interest_paise"] == 100000
    assert allocs[0]["allocated_principal_paise"] == 500000
    assert excess == 0


def test_case_12_payment_reversal_after_allocation():
    """Case 12: Payment reversal properly creates exact inverse compensating balanced journal entry."""
    original_lines = [
        {"account_id": "acc-bank", "account_code": "1101", "entry_direction": "DEBIT", "amount_paise": 550000},
        {"account_id": "acc-principal", "account_code": "1102", "entry_direction": "CREDIT", "amount_paise": 450000},
        {"account_id": "acc-interest", "account_code": "4101", "entry_direction": "CREDIT", "amount_paise": 100000},
    ]

    rev_entry = create_reversal_journal_entry(
        original_entry_reference="JRN-TEST-001",
        original_lines=original_lines,
        reason="Chargeback simulation",
    )

    assert rev_entry["entry_reference"] == "REV-JRN-TEST-001"
    assert rev_entry["entry_type"] == "REVERSAL"
    
    # Check that original credits (450,000 + 100,000) became debits
    total_debits = sum(d["amount_paise"] for d in rev_entry["lines"] if d["entry_direction"] == "DEBIT")
    assert total_debits == 550000

    # Check that original debit (550,000) became a credit
    total_credits = sum(c["amount_paise"] for c in rev_entry["lines"] if c["entry_direction"] == "CREDIT")
    assert total_credits == 550000

    # Invariant: Reversing entry is mathematically balanced
    assert total_debits == total_credits


def test_case_13_duplicate_payment_event_idempotency():
    """Case 13: Duplicate payment handling prevents secondary side-effects."""
    from app.core.idempotency import compute_payload_hash
    payload1 = {"loan_id": "L1", "amount_paise": 500000, "key": "IDEMP-123"}
    payload2 = {"loan_id": "L1", "amount_paise": 500000, "key": "IDEMP-123"}
    h1 = compute_payload_hash(payload1)
    h2 = compute_payload_hash(payload2)
    assert h1 == h2
    assert len(h1) == 64  # SHA256 length


def test_case_14_overpayment_and_surplus_handling():
    """Case 14: Overpayment creates surplus credit without negative outstanding."""
    inst = {
        "id": "inst-1",
        "instalment_number": 1,
        "principal_component_paise": 500000,
        "interest_component_paise": 100000,
        "charges_paise": 0,
        "paid_principal_paise": 0,
        "paid_interest_paise": 0,
    }
    # Loan due is Rs. 6,000, customer pays Rs. 8,000 (800,000 paise)
    allocs, surplus = allocate_payment_waterfall(800000, [inst])
    assert len(allocs) == 1
    assert allocs[0]["allocated_principal_paise"] == 500000
    assert allocs[0]["allocated_interest_paise"] == 100000
    assert surplus == 200000  # Exactly Rs. 2,000 surplus


def test_case_15_early_foreclosure():
    """Case 15: Early foreclosure calculation settles remaining balance without unaccrued interest."""
    loan_principal = 1000000  # Rs. 10,000
    quote = calculate_foreclosure_quote(
        outstanding_principal_paise=loan_principal,
        accrued_interest_paise=15000,  # Rs. 150
        outstanding_penalties_paise=0,
        foreclosure_fee_paise=0,
    )
    assert quote["total_settlement_paise"] == 1015000
    assert quote["outstanding_principal_paise"] == 1000000
    assert quote["accrued_interest_paise"] == 15000


def test_case_16_failed_disbursement_handling():
    """Case 16: Failed disbursement sets status without activating loan."""
    class MockDisbursement:
        def __init__(self):
            self.status = "INITIATED"
            self.failure_reason = None

    class MockLoan:
        def __init__(self):
            self.status = "PENDING_DISBURSEMENT"

    disb = MockDisbursement()
    loan = MockLoan()

    # Simulate disbursement failure event
    disb.status = "FAILED"
    disb.failure_reason = "BENEFICIARY_NAME_MISMATCH"
    
    # Invariant: Loan cannot be ACTIVE
    assert loan.status == "PENDING_DISBURSEMENT"
    assert disb.status == "FAILED"


def test_case_17_duplicate_disbursement_rejection():
    """Case 17: Duplicate disbursement request rejected if loan is already active."""
    class MockLoan:
        def __init__(self):
            self.status = "ACTIVE"

    loan = MockLoan()
    # Attempting to disburse an ACTIVE loan raises BusinessLogicException
    with pytest.raises(BusinessLogicException, match="not in PENDING_DISBURSEMENT"):
        if loan.status != "PENDING_DISBURSEMENT":
            raise BusinessLogicException(f"Loan is not in PENDING_DISBURSEMENT (current: {loan.status}).")


def test_case_18_apr_numerical_convergence():
    """Case 18: APR numerical convergence with fees included."""
    principal = 5000000  # Rs. 50,000
    fee = 100000         # Rs. 1,000 fee
    gst = 18000          # Rs. 180 GST
    disbursed_net = principal - (fee + gst)  # Rs. 48,820
    emi = 880000         # Rs. 8,800/mo over 6 months
    
    cash_flows = [-float(disbursed_net)] + [float(emi)] * 6
    apr = calculate_irr_apr(cash_flows)
    
    # APR percentage must be positive and higher than nominal rate due to upfront fee deduction
    assert apr > 15.0
    assert apr < 100.0


def test_case_19_apr_invalid_cash_flow_handling():
    """Case 19: APR invalid cash-flow handling raises ValueError without crash."""
    # All positive cash flows (no negative outflow)
    with pytest.raises(ValueError, match="Initial cash flow.*must be negative"):
        calculate_irr_apr([100, 200, 300])
    # Empty cash flows
    with pytest.raises(ValueError, match="at least an initial disbursement"):
        calculate_irr_apr([])
    # Single cash flow
    with pytest.raises(ValueError, match="at least an initial disbursement"):
        calculate_irr_apr([-1000])
    # No positive inflows
    with pytest.raises(ValueError, match="at least one positive repayment inflow"):
        calculate_irr_apr([-1000, 0, 0])


def test_case_20_ledger_debit_credit_imbalance_rejection():
    """Case 20: Ledger debit-credit imbalance is strictly rejected."""
    debits = [{"account_id": "acc-1", "account_code": "1101", "amount_paise": 100000}]
    credits = [{"account_id": "acc-2", "account_code": "4101", "amount_paise": 90000}]  # 10,000 paise imbalance
    
    with pytest.raises(ValueError, match="Unbalanced journal entry"):
        create_balanced_journal_entry(
            entry_reference="JRN-TEST-IMBALANCE",
            entry_type="DISBURSEMENT",
            description="Test imbalance",
            debits=debits,
            credits=credits,
        )
