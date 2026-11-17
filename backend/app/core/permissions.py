from enum import Enum
from typing import List, Set


class RoleEnum(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    OPERATIONS_ADMIN = "OPERATIONS_ADMIN"
    KYC_OFFICER = "KYC_OFFICER"
    UNDERWRITER = "UNDERWRITER"
    FINANCE_OFFICER = "FINANCE_OFFICER"
    CUSTOMER_SUPPORT = "CUSTOMER_SUPPORT"
    CUSTOMER = "CUSTOMER"


class PermissionEnum(str, Enum):
    # Customer
    CUSTOMER_READ = "customer:read"
    CUSTOMER_WRITE = "customer:write"
    
    # KYC
    KYC_REVIEW = "kyc:review"
    KYC_DECIDE = "kyc:decide"
    
    # Underwriting & Applications
    APPLICATION_READ = "application:read"
    APPLICATION_DECIDE = "application:decide"
    PRODUCT_MANAGE = "product:manage"
    
    # Finance & Disbursement
    DISBURSEMENT_TRIGGER = "disbursement:trigger"
    REPAYMENT_MANAGE = "repayment:manage"
    LEDGER_VIEW = "ledger:view"
    LEDGER_POST = "ledger:post"
    
    # Support
    SUPPORT_READ = "support:read"
    SUPPORT_RESPOND = "support:respond"
    
    # Admin System
    USER_MANAGE = "user:manage"
    AUDIT_VIEW = "audit:view"
    METRICS_VIEW = "metrics:view"


# Role to permissions mapping
ROLE_PERMISSIONS: dict[RoleEnum, Set[PermissionEnum]] = {
    RoleEnum.SUPER_ADMIN: set(PermissionEnum),  # All permissions
    RoleEnum.OPERATIONS_ADMIN: {
        PermissionEnum.CUSTOMER_READ,
        PermissionEnum.CUSTOMER_WRITE,
        PermissionEnum.KYC_REVIEW,
        PermissionEnum.KYC_DECIDE,
        PermissionEnum.APPLICATION_READ,
        PermissionEnum.APPLICATION_DECIDE,
        PermissionEnum.PRODUCT_MANAGE,
        PermissionEnum.DISBURSEMENT_TRIGGER,
        PermissionEnum.REPAYMENT_MANAGE,
        PermissionEnum.LEDGER_VIEW,
        PermissionEnum.SUPPORT_READ,
        PermissionEnum.SUPPORT_RESPOND,
        PermissionEnum.AUDIT_VIEW,
        PermissionEnum.METRICS_VIEW,
    },
    RoleEnum.KYC_OFFICER: {
        PermissionEnum.CUSTOMER_READ,
        PermissionEnum.KYC_REVIEW,
        PermissionEnum.KYC_DECIDE,
        PermissionEnum.AUDIT_VIEW,
    },
    RoleEnum.UNDERWRITER: {
        PermissionEnum.CUSTOMER_READ,
        PermissionEnum.APPLICATION_READ,
        PermissionEnum.APPLICATION_DECIDE,
        PermissionEnum.AUDIT_VIEW,
    },
    RoleEnum.FINANCE_OFFICER: {
        PermissionEnum.DISBURSEMENT_TRIGGER,
        PermissionEnum.REPAYMENT_MANAGE,
        PermissionEnum.LEDGER_VIEW,
        PermissionEnum.LEDGER_POST,
        PermissionEnum.AUDIT_VIEW,
        PermissionEnum.METRICS_VIEW,
    },
    RoleEnum.CUSTOMER_SUPPORT: {
        PermissionEnum.CUSTOMER_READ,
        PermissionEnum.SUPPORT_READ,
        PermissionEnum.SUPPORT_RESPOND,
        PermissionEnum.APPLICATION_READ,
    },
    RoleEnum.CUSTOMER: {
        PermissionEnum.CUSTOMER_READ,
        PermissionEnum.CUSTOMER_WRITE,
    },
}


def role_has_permission(role: RoleEnum, permission: PermissionEnum) -> bool:
    permissions = ROLE_PERMISSIONS.get(role, set())
    return permission in permissions
