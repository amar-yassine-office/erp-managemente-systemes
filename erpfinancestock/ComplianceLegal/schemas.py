from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ComplianceCheckCreateSchema(BaseModel):
    user_id: int
    check_type: str
    status: str = "FLAGGED"
    notes: Optional[str] = None
    next_review_date: Optional[date] = None


class ComplianceCheckUpdateSchema(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    next_review_date: Optional[date] = None


class ComplianceCheckOutSchema(BaseModel):
    id: int
    user_id: int
    check_type: str
    status: str
    notes: Optional[str]
    performed_by_id: Optional[int]
    checked_at: datetime
    next_review_date: Optional[date]

    class Config:
        from_attributes = True


class RestrictedAssetCreateSchema(BaseModel):
    symbol: str
    company_name: str
    reason: str
    description: Optional[str] = None
    is_active: bool = True
    start_date: date
    end_date: Optional[date] = None


class RestrictedAssetUpdateSchema(BaseModel):
    company_name: Optional[str] = None
    reason: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class RestrictedAssetOutSchema(BaseModel):
    id: int
    symbol: str
    company_name: str
    reason: str
    description: Optional[str]
    is_active: bool
    start_date: date
    end_date: Optional[date]
    added_by_id: Optional[int]

    class Config:
        from_attributes = True


class SuspiciousActivityReportCreateSchema(BaseModel):
    user_id: int
    portfolio_account_number: Optional[str] = None
    title: str
    description: str
    severity: str = "MEDIUM"
    status: str = "UNDER_REVIEW"


class SuspiciousActivityReportUpdateSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None


class SuspiciousActivityReportOutSchema(BaseModel):
    id: int
    user_id: int
    portfolio_account_number: Optional[str]
    title: str
    description: str
    severity: str
    status: str
    investigated_by_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TradeSurveillanceRuleCreateSchema(BaseModel):
    rule_name: str
    rule_type: str
    description: str
    threshold_value: Decimal
    is_active: bool = True


class TradeSurveillanceRuleUpdateSchema(BaseModel):
    rule_name: Optional[str] = None
    rule_type: Optional[str] = None
    description: Optional[str] = None
    threshold_value: Optional[Decimal] = None
    is_active: Optional[bool] = None


class TradeSurveillanceRuleOutSchema(BaseModel):
    id: int
    rule_name: str
    rule_type: str
    description: str
    threshold_value: Decimal
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogOutSchema(BaseModel):
    id: int
    actor_id: Optional[int]
    action_type: str
    target_model: str
    target_id: Optional[str]
    ip_address: Optional[str]
    changes: Dict[str, Any]
    timestamp: datetime

    class Config:
        from_attributes = True