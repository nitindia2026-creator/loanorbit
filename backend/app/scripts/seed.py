import asyncio
from datetime import date, datetime, timedelta, timezone
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, Base, async_engine
from app.core.permissions import RoleEnum
from app.core.security import get_password_hash
from app.financial.emi import calculate_fee_and_gst, calculate_monthly_emi
from app.financial.schedule import generate_amortisation_schedule
from app.models.application import LoanApplication, UnderwritingDecision
from app.models.bank import BankVerification
from app.models.document import SupportMessage, SupportTicket
from app.models.kyc import KYCCase
from app.models.ledger import LedgerAccount
from app.models.loan import Instalment, Loan
from app.models.offer import LoanOffer
from app.models.product import LoanProduct, LoanProductVersion
from app.models.profile import CustomerProfile
from app.models.repayment import Disbursement, Payment, PaymentAllocation
from app.models.user import AdminUser, User


async def run_seed():
    print("🌱 Starting LOANORBIT Idempotent Data Seeding...")

    # Ensure tables exist
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # ==========================================
        # 1. Seed Chart of Accounts
        # ==========================================
        accounts_data = [
            ("1001", "Cash / Settlement Pool", "ASSET"),
            ("1101", "Loan Principal Receivable", "ASSET"),
            ("1102", "Interest Receivable", "ASSET"),
            ("1103", "Penalties Receivable", "ASSET"),
            ("2001", "Borrower Overpayment Holding", "LIABILITY"),
            ("2101", "GST Payable on Fees", "LIABILITY"),
            ("3001", "Capital / Equity", "EQUITY"),
            ("4001", "Interest Income", "REVENUE"),
            ("4002", "Processing Fee Income", "REVENUE"),
        ]
        for code, name, acc_type in accounts_data:
            stmt = select(LedgerAccount).where(LedgerAccount.account_code == code)
            exists = (await session.execute(stmt)).scalar_one_or_none()
            if not exists:
                session.add(LedgerAccount(account_code=code, account_name=name, account_type=acc_type))
        await session.flush()
        print("✅ Chart of Accounts seeded.")

        # ==========================================
        # 2. Seed Admin Users (All 6 Roles)
        # ==========================================
        admin_pass_hash = get_password_hash("AdminPass123!")
        admins_data = [
            ("superadmin", "superadmin@loanorbit.demo", "Super Admin Officer", RoleEnum.SUPER_ADMIN),
            ("ops_lead", "ops@loanorbit.demo", "Operations Manager", RoleEnum.OPERATIONS_ADMIN),
            ("kyc_lead", "kyc@loanorbit.demo", "Senior KYC Officer", RoleEnum.KYC_OFFICER),
            ("underwriter_lead", "underwriter@loanorbit.demo", "Credit Underwriter Lead", RoleEnum.UNDERWRITER),
            ("finance_lead", "finance@loanorbit.demo", "Chief Finance Controller", RoleEnum.FINANCE_OFFICER),
            ("support_lead", "support@loanorbit.demo", "Customer Care Lead", RoleEnum.CUSTOMER_SUPPORT),
        ]
        for uname, uemail, fname, role in admins_data:
            stmt = select(AdminUser).where(AdminUser.username == uname)
            exists = (await session.execute(stmt)).scalar_one_or_none()
            if not exists:
                session.add(AdminUser(
                    username=uname,
                    email=uemail,
                    full_name=fname,
                    hashed_password=admin_pass_hash,
                    role=role,
                ))
        await session.flush()
        print("✅ All 6 Admin Roles seeded.")

        # ==========================================
        # 3. Seed Loan Products
        # ==========================================
        products_data = [
            ("SALARIED_STARTER", "Salaried Express Starter", "Instant credit for salaried professionals", 1000000, 3000000, "3,6", 1800, "PERCENTAGE", 200),
            ("CREDIT_BUILDER", "Credit Builder Loan", "Small ticket micro loan designed to establish credit score", 500000, 1500000, "3,6,12", 1500, "FIXED", 30000),
            ("GROWTH_PERSONAL", "Personal Growth Advance", "Medium ticket loan for unexpected medical or travel expenses", 2500000, 10000000, "6,12,24", 2100, "PERCENTAGE", 250),
        ]
        prod_version_map = {}
        for pcode, pname, pdesc, min_p, max_p, tenures, rate_bps, fee_type, fee_val in products_data:
            stmt = select(LoanProduct).where(LoanProduct.code == pcode)
            prod = (await session.execute(stmt)).scalar_one_or_none()
            if not prod:
                prod = LoanProduct(code=pcode, name=pname, description=pdesc)
                session.add(prod)
                await session.flush()

                version = LoanProductVersion(
                    product_id=prod.id,
                    version_number=1,
                    min_principal_paise=min_p,
                    max_principal_paise=max_p,
                    available_tenures_months=tenures,
                    annual_nominal_interest_rate_bps=rate_bps,
                    processing_fee_type=fee_type,
                    processing_fee_value=fee_val,
                    gst_rate_bps=1800,
                    late_charge_daily_bps=5,
                )
                session.add(version)
                await session.flush()
                prod_version_map[pcode] = version
            else:
                stmt_v = select(LoanProductVersion).where(LoanProductVersion.product_id == prod.id)
                v = (await session.execute(stmt_v)).scalars().first()
                prod_version_map[pcode] = v
        print("✅ 3 Versioned Loan Products seeded.")

        # ==========================================
        # 4. Seed Synthetic Customers 01 to 07
        # ==========================================
        customers_data = [
            ("01", "+919800000001", "Arjun Mehta", "ELIGIBLE"),
            ("02", "+919800000002", "Priya Verma", "KYC_PENDING"),
            ("03", "+919800000003", "Rahul Sharma", "KYC_REJECTED"),
            ("04", "+919800000004", "Ananya Deshmukh", "UNDER_REVIEW"),
            ("05", "+919800000005", "Vikram Patel", "ACTIVE_LOAN"),
            ("06", "+919800000006", "Sneha Nair", "OVERDUE_LOAN"),
            ("07", "+919800000007", "Rohan Iyer", "REPAID_LOAN"),
        ]

        cust_map = {}
        for cid, mob, cname, persona in customers_data:
            stmt = select(User).where(User.mobile_number == mob)
            user = (await session.execute(stmt)).scalar_one_or_none()
            if not user:
                user = User(
                    mobile_number=mob,
                    email=f"customer{cid}@loanorbit.demo",
                    is_active=True,
                    is_verified=True,
                )
                session.add(user)
                await session.flush()

                # Customer Profile
                income_paise = 4500000 if cid != "03" else 1200000
                prof = CustomerProfile(
                    user_id=user.id,
                    full_name=cname,
                    date_of_birth=date(1995, 4, 15),
                    gender="MALE" if cid in ["01", "03", "05", "07"] else "FEMALE",
                    address_line1="402, Green Glen Tech Park",
                    city="Bengaluru",
                    state="Karnataka",
                    pincode="560103",
                    employment_type="SALARIED",
                    monthly_income_paise=income_paise,
                    monthly_expenses_paise=1500000,
                    employer_name="Orbit Software Labs India",
                    employment_duration_months=24,
                )
                session.add(prof)

                # Bank Verification
                bank = BankVerification(
                    user_id=user.id,
                    account_holder_name=cname,
                    bank_name="HDFC Bank",
                    account_number_masked=f"XXXXXX{cid}001",
                    ifsc_code="HDFC0001234",
                    status="VERIFIED" if cid != "02" else "PENDING",
                    penny_drop_reference=f"PND-{cid}001",
                    verified_at=datetime.now(timezone.utc) if cid != "02" else None,
                )
                session.add(bank)

                # KYC Case
                kyc_status = "VERIFIED"
                rejection_msg = None
                if cid == "02":
                    kyc_status = "PENDING"
                elif cid == "03":
                    kyc_status = "REJECTED"
                    rejection_msg = "Synthetic PAN card details blurred and unreadable."

                kyc = KYCCase(
                    user_id=user.id,
                    id_type="PAN",
                    id_number_masked=f"ABCDE{cid}01F",
                    status=kyc_status,
                    rejection_reason=rejection_msg,
                )
                session.add(kyc)
                await session.flush()

            cust_map[cid] = user
        await session.flush()
        print("✅ 7 Synthetic Customer Personas created.")

        # ==========================================
        # 5. Seed Customer 04: Application Under Review
        # ==========================================
        c4 = cust_map["04"]
        stmt_app = select(LoanApplication).where(LoanApplication.user_id == c4.id)
        if not (await session.execute(stmt_app)).scalar_one_or_none():
            app4 = LoanApplication(
                application_reference="APP-SEED-04",
                user_id=c4.id,
                product_version_id=prod_version_map["SALARIED_STARTER"].id,
                requested_amount_paise=2500000,
                requested_tenure_months=6,
                purpose="Emergency medical expense simulation",
                status="UNDER_REVIEW",
            )
            session.add(app4)

        # ==========================================
        # 6. Seed Customer 05: Approved Active Loan
        # ==========================================
        c5 = cust_map["05"]
        stmt_lon = select(Loan).where(Loan.user_id == c5.id)
        if not (await session.execute(stmt_lon)).scalar_one_or_none():
            app5 = LoanApplication(
                application_reference="APP-SEED-05",
                user_id=c5.id,
                product_version_id=prod_version_map["SALARIED_STARTER"].id,
                requested_amount_paise=2000000,
                requested_tenure_months=6,
                purpose="Home office tech purchase",
                status="DISBURSED",
            )
            session.add(app5); await session.flush()

            ofr5 = LoanOffer(
                application_id=app5.id,
                offer_reference="OFR-SEED-05",
                offered_amount_paise=2000000,
                tenure_months=6,
                annual_nominal_interest_rate_bps=1800,
                monthly_emi_paise=351000,
                processing_fee_paise=40000,
                gst_paise=7200,
                net_disbursement_paise=1952800,
                total_repayable_paise=2106000,
                apr_bps=2450,
                status="ACCEPTED",
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            )
            session.add(ofr5); await session.flush()

            lon5 = Loan(
                loan_reference="LON-SEED-05",
                user_id=c5.id,
                application_id=app5.id,
                offer_id=ofr5.id,
                principal_paise=2000000,
                outstanding_principal_paise=2000000,
                outstanding_interest_paise=106000,
                status="ACTIVE",
                disbursed_at=datetime.now(timezone.utc) - timedelta(days=15),
            )
            session.add(lon5); await session.flush()

            sch5 = generate_amortisation_schedule(2000000, 1800, 6, date.today() - timedelta(days=15))
            for s in sch5:
                session.add(Instalment(
                    loan_id=lon5.id,
                    instalment_number=s["instalment_number"],
                    due_date=s["due_date"],
                    opening_principal_paise=s["opening_principal_paise"],
                    emi_amount_paise=s["emi_amount_paise"],
                    principal_component_paise=s["principal_component_paise"],
                    interest_component_paise=s["interest_component_paise"],
                    closing_principal_paise=s["closing_principal_paise"],
                    outstanding_amount_paise=s["emi_amount_paise"],
                    status="SCHEDULED",
                ))

            # Disbursement record
            stmt_bank = select(BankVerification).where(BankVerification.user_id == c5.id)
            b5 = (await session.execute(stmt_bank)).scalars().first()
            session.add(Disbursement(
                loan_id=lon5.id,
                amount_paise=1952800,
                bank_verification_id=b5.id,
                mock_provider_reference="LND-DISB-SEED-05",
                status="SUCCESS",
                disbursed_at=datetime.now(timezone.utc) - timedelta(days=15),
            ))

        # ==========================================
        # 7. Seed Customer 06: Overdue Loan
        # ==========================================
        c6 = cust_map["06"]
        stmt_lon6 = select(Loan).where(Loan.user_id == c6.id)
        if not (await session.execute(stmt_lon6)).scalar_one_or_none():
            app6 = LoanApplication(
                application_reference="APP-SEED-06",
                user_id=c6.id,
                product_version_id=prod_version_map["CREDIT_BUILDER"].id,
                requested_amount_paise=1000000,
                requested_tenure_months=3,
                purpose="Course fees advance",
                status="DISBURSED",
            )
            session.add(app6); await session.flush()

            ofr6 = LoanOffer(
                application_id=app6.id,
                offer_reference="OFR-SEED-06",
                offered_amount_paise=1000000,
                tenure_months=3,
                annual_nominal_interest_rate_bps=1500,
                monthly_emi_paise=341700,
                processing_fee_paise=30000,
                gst_paise=5400,
                net_disbursement_paise=964600,
                total_repayable_paise=1025100,
                apr_bps=2200,
                status="ACCEPTED",
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            )
            session.add(ofr6); await session.flush()

            lon6 = Loan(
                loan_reference="LON-SEED-06",
                user_id=c6.id,
                application_id=app6.id,
                offer_id=ofr6.id,
                principal_paise=1000000,
                outstanding_principal_paise=1000000,
                outstanding_interest_paise=25100,
                outstanding_penalties_paise=5000,
                status="OVERDUE",
                disbursed_at=datetime.now(timezone.utc) - timedelta(days=45),
            )
            session.add(lon6); await session.flush()

            sch6 = generate_amortisation_schedule(1000000, 1500, 3, date.today() - timedelta(days=45))
            for s in sch6:
                st = "OVERDUE" if s["instalment_number"] == 1 else "SCHEDULED"
                session.add(Instalment(
                    loan_id=lon6.id,
                    instalment_number=s["instalment_number"],
                    due_date=s["due_date"],
                    opening_principal_paise=s["opening_principal_paise"],
                    emi_amount_paise=s["emi_amount_paise"],
                    principal_component_paise=s["principal_component_paise"],
                    interest_component_paise=s["interest_component_paise"],
                    closing_principal_paise=s["closing_principal_paise"],
                    outstanding_amount_paise=s["emi_amount_paise"],
                    status=st,
                ))

        # ==========================================
        # 8. Seed Customer 07: Fully Repaid Loan
        # ==========================================
        c7 = cust_map["07"]
        stmt_lon7 = select(Loan).where(Loan.user_id == c7.id)
        if not (await session.execute(stmt_lon7)).scalar_one_or_none():
            app7 = LoanApplication(
                application_reference="APP-SEED-07",
                user_id=c7.id,
                product_version_id=prod_version_map["CREDIT_BUILDER"].id,
                requested_amount_paise=500000,
                requested_tenure_months=3,
                purpose="Smartphone purchase",
                status="DISBURSED",
            )
            session.add(app7); await session.flush()

            ofr7 = LoanOffer(
                application_id=app7.id,
                offer_reference="OFR-SEED-07",
                offered_amount_paise=500000,
                tenure_months=3,
                annual_nominal_interest_rate_bps=1500,
                monthly_emi_paise=170850,
                processing_fee_paise=30000,
                gst_paise=5400,
                net_disbursement_paise=464600,
                total_repayable_paise=512550,
                apr_bps=2150,
                status="ACCEPTED",
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            )
            session.add(ofr7); await session.flush()

            lon7 = Loan(
                loan_reference="LON-SEED-07",
                user_id=c7.id,
                application_id=app7.id,
                offer_id=ofr7.id,
                principal_paise=500000,
                outstanding_principal_paise=0,
                outstanding_interest_paise=0,
                status="CLOSED",
                disbursed_at=datetime.now(timezone.utc) - timedelta(days=90),
                closed_at=datetime.now(timezone.utc) - timedelta(days=5),
            )
            session.add(lon7); await session.flush()

            # Record completed payment
            pay7 = Payment(
                loan_id=lon7.id,
                amount_paise=512550,
                payment_method="UPI_MOCK",
                status="SUCCESS",
                provider_reference="NPCI-SEED-07-PAID",
                paid_at=datetime.now(timezone.utc) - timedelta(days=5),
            )
            session.add(pay7)

        # ==========================================
        # 9. Seed Sample Support Ticket
        # ==========================================
        stmt_tck = select(SupportTicket).where(SupportTicket.user_id == c5.id)
        if not (await session.execute(stmt_tck)).scalar_one_or_none():
            tck = SupportTicket(
                ticket_reference="TCK-SEED-101",
                user_id=c5.id,
                category="PAYMENT",
                subject="Query regarding early prepayment discount",
                description="Hello LOANORBIT, can I foreclose my personal loan without lock-in penalties?",
                status="OPEN",
            )
            session.add(tck); await session.flush()
            session.add(SupportMessage(
                ticket_id=tck.id,
                sender_type="CUSTOMER",
                sender_id=c5.id,
                message=tck.description,
            ))

        await session.commit()
        print("🎉 LOANORBIT Idempotent Seeding Completed Successfully!")


if __name__ == "__main__":
    asyncio.run(run_seed())
