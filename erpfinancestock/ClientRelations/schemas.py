from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr


# =====================================================================
# 1. CLIENT PROFILE SCHEMAS
# =====================================================================

class ClientProfileCreateSchema(BaseModel):
    user_id: int
    client_type: Optional[str] = "INDIVIDUAL"
    phone_number: Optional[str] = ""
    tax_id: Optional[str] = ""
    address: Optional[str] = ""
    risk_tolerance: Optional[str] = "MODERATE"
    net_worth_estimate: Optional[Decimal] = None
    investment_goal: Optional[str] = ""
    relationship_manager_id: Optional[int] = None


class ClientProfileUpdateSchema(BaseModel):
    client_type: Optional[str] = None
    phone_number: Optional[str] = None
    tax_id: Optional[str] = None
    address: Optional[str] = None
    risk_tolerance: Optional[str] = None
    net_worth_estimate: Optional[Decimal] = None
    investment_goal: Optional[str] = None
    relationship_manager_id: Optional[int] = None


class ClientProfileOutSchema(BaseModel):
    id: int
    user_id: int
    client_type: str
    phone_number: str
    tax_id: str
    address: str
    risk_tolerance: str
    net_worth_estimate: Optional[Decimal]
    investment_goal: str
    relationship_manager_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =====================================================================
# 2. KYC DOCUMENT SCHEMAS
# =====================================================================

class KYCDocumentCreateSchema(BaseModel):
    client_id: int
    document_type: str
    document_number: Optional[str] = ""
    expiry_date: Optional[date] = None


class KYCDocumentUpdateSchema(BaseModel):
    status: Optional[str] = None
    rejection_reason: Optional[str] = None
    expiry_date: Optional[date] = None


class KYCDocumentOutSchema(BaseModel):
    id: int
    client_id: int
    document_type: str
    document_number: str
    file: str
    status: str
    rejection_reason: str
    expiry_date: Optional[date]
    uploaded_at: datetime
    verified_at: Optional[datetime]

    class Config:
        from_attributes = True


# =====================================================================
# 3. INTERACTION LOG SCHEMAS
# =====================================================================

class InteractionLogCreateSchema(BaseModel):
    client_id: int
    channel: Optional[str] = "EMAIL"
    subject: str = Field(..., max_length=255)
    summary: str
    follow_up_required: Optional[bool] = False
    follow_up_date: Optional[date] = None


class InteractionLogOutSchema(BaseModel):
    id: int
    client_id: int
    staff_member_id: Optional[int]
    channel: str
    subject: str
    summary: str
    follow_up_required: bool
    follow_up_date: Optional[date]
    created_at: datetime

    class Config:
        from_attributes = True


# =====================================================================
# 4. LEAD PIPELINE SCHEMAS
# =====================================================================

class LeadPipelineCreateSchema(BaseModel):
    full_name: str = Field(..., max_length=150)
    email: EmailStr
    phone: Optional[str] = ""
    company_name: Optional[str] = ""
    estimated_investment_amount: Optional[Decimal] = None
    stage: Optional[str] = "NEW"
    assigned_to_id: Optional[int] = None
    notes: Optional[str] = ""


class LeadPipelineUpdateSchema(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company_name: Optional[str] = None
    estimated_investment_amount: Optional[Decimal] = None
    stage: Optional[str] = None
    assigned_to_id: Optional[int] = None
    notes: Optional[str] = None


class LeadPipelineOutSchema(BaseModel):
    id: int
    full_name: str
    email: str
    phone: str
    company_name: str
    estimated_investment_amount: Optional[Decimal]
    stage: str
    assigned_to_id: Optional[int]
    notes: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True