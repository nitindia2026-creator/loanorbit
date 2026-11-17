from app.schemas.auth import Token, OTPRequest, OTPResponse, OTPVerifyRequest, AdminLoginRequest
from app.schemas.customer import ProfileCreateOrUpdate, ProfileResponse, ConsentCreate, ConsentResponse
from app.schemas.kyc import KYCCaseResponse, KYCDecisionRequest, BankVerificationRequest, BankVerificationResponse
from app.schemas.product import LoanProductResponse, CalculatorRequest, CalculatorResponse
from app.schemas.application import ApplicationCreate, ApplicationResponse, UnderwritingDecisionRequest, LoanOfferResponse, LoanResponse, RepaymentRequest, ForeclosureQuoteResponse
from app.schemas.ledger import LedgerAccountResponse, JournalEntryResponse
from app.schemas.admin import DashboardMetricsResponse
