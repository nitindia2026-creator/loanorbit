from datetime import date
import pytest
from app.financial.emi import calculate_monthly_emi, calculate_fee_and_gst
from app.financial.schedule import generate_amortisation_schedule
from app.financial.apr import calculate_irr_apr
from app.financial.allocation import allocate_payment_waterfall
from app.financial.ledger import create_balanced_journal_entry
from app.financial.prepayment import calculate_foreclosure_quote


def test_emi_calculation_standard():
    # Principal: ₹25,000 (2,500,000 paise), Annual Rate: 18% (1800 bps), Tenure: 6 months
    principal_paise = 2500000
    rate_bps = 1800
    tenure_months = 6

    emi_paise = calculate_monthly_emi(principal_paise, rate_bps, tenure_months)
    # Expected EMI is approx ₹4,388 (438,780 paise)
    assert 438000 <= emi_paise <= 440000
    assert isinstance(emi_paise, int)


def test_emi_calculation_zero_interest():
    # Principal: ₹30,000 (3,000,000 paise), 0% interest, 3 months
    principal_paise = 3000000
    rate_bps = 0
    tenure_months = 3

    emi_paise = calculate_monthly_emi(principal_paise, rate_bps, tenure_months)
    assert emi_paise == 1000000  # Exactly ₹10,000 (1,000,000 paise)


def test_fee_and_gst_calculation():
    # Principal: ₹50,000 (5,000,000 paise), 2% processing fee (200 bps), 18% GST (1800 bps)
    principal_paise = 5000000
    fee_paise, gst_paise, net_disb_paise = calculate_fee_and_gst(
        principal_paise=principal_paise,
        fee_type="PERCENTAGE",
        fee_value=200,
        gst_rate_bps=1800,
    )

    assert fee_paise == 100000  # ₹1,000 (2% of 50,000)
    assert gst_paise == 18000   # ₹180 (18% of 1,000)
    assert net_disb_paise == 5000000 - 118000  # ₹48,820 (4,882,000 paise)


def test_amortisation_schedule_invariants():
    principal_paise = 2500000
    rate_bps = 1800
    tenure_months = 6
    start = date(2026, 1, 1)

    schedule = generate_amortisation_schedule(principal_paise, rate_bps, tenure_months, start)

    assert len(schedule) == tenure_months

    # Check invariant 1: sum of principal components == disbursed principal
    total_principal_paid = sum(item["principal_component_paise"] for item in schedule)
    assert total_principal_paid == principal_paise

    # Check invariant 2: final closing principal == 0
    assert schedule[-1]["closing_principal_paise"] == 0

    # Check invariant 3: opening principal of period k+1 == closing of period k
    for k in range(len(schedule) - 1):
        assert schedule[k + 1]["opening_principal_paise"] == schedule[k]["closing_principal_paise"]


def test_apr_calculation():
    # Outflow: -₹24,410 | Inflow: 6 monthly payments of ₹4,388
    cash_flows = [-24410.0] + [4388.0] * 6
    apr = calculate_irr_apr(cash_flows)
    # Effective APR including fees will be higher than nominal 18%
    assert 20.0 <= apr <= 30.0


def test_payment_allocation_waterfall():
    instalments = [
        {
            "id": "inst-1",
            "instalment_number": 1,
            "interest_component_paise": 37500,
            "principal_component_paise": 401300,
            "charges_paise": 5000,
            "paid_interest_paise": 0,
            "paid_principal_paise": 0,
        },
        {
            "id": "inst-2",
            "instalment_number": 2,
            "interest_component_paise": 31500,
            "principal_component_paise": 407300,
            "charges_paise": 0,
            "paid_interest_paise": 0,
            "paid_principal_paise": 0,
        }
    ]

    # Partial payment of ₹200 (20,000 paise): covers 5,000 charges + 15,000 partial interest
    allocs, excess = allocate_payment_waterfall(20000, instalments)
    assert len(allocs) == 1
    assert allocs[0]["allocated_charges_paise"] == 5000
    assert allocs[0]["allocated_interest_paise"] == 15000
    assert allocs[0]["allocated_principal_paise"] == 0
    assert excess == 0


def test_balanced_general_ledger():
    # Valid balanced entry
    entry = create_balanced_journal_entry(
        entry_reference="DISB-1001",
        entry_type="DISBURSEMENT",
        description="Loan payout",
        debits=[{"account_id": "acc-1101", "amount_paise": 2500000}],
        credits=[
            {"account_id": "acc-1001", "amount_paise": 2441000},
            {"account_id": "acc-4002", "amount_paise": 50000},
            {"account_id": "acc-2101", "amount_paise": 9000},
        ]
    )
    assert entry["total_amount_paise"] == 2500000

    # Unbalanced entry must raise ValueError
    with pytest.raises(ValueError):
        create_balanced_journal_entry(
            entry_reference="BAD-1",
            entry_type="DISBURSEMENT",
            description="Bad entry",
            debits=[{"account_id": "acc-1", "amount_paise": 1000}],
            credits=[{"account_id": "acc-2", "amount_paise": 900}],
        )


def test_foreclosure_calculation():
    quote = calculate_foreclosure_quote(
        outstanding_principal_paise=1200000,
        accrued_interest_paise=15000,
        outstanding_penalties_paise=5000,
        foreclosure_fee_paise=0,
    )
    assert quote["total_settlement_paise"] == 1220000
