from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


# =====================================================================
# 1. SYSTEM SERVER SCHEMAS
# =====================================================================

class SystemServerCreateSchema(BaseModel):
    name: str = Field(..., max_length=100, example="app-worker-01")
    ip_address: str = Field(..., example="192.168.1.50")
    server_type: str = Field("APP", example="APP", description="APP, DB, CACHE, or WORKER")
    status: str = Field("ONLINE", example="ONLINE", description="ONLINE, DEGRADED, OFFLINE, or MAINTENANCE")
    cpu_usage_pct: Decimal = Field(Decimal("0.00"), ge=0, le=100, example="12.50")
    memory_usage_pct: Decimal = Field(Decimal("0.00"), ge=0, le=100, example="45.80")


class SystemServerUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    ip_address: Optional[str] = Field(None)
    server_type: Optional[str] = Field(None, description="APP, DB, CACHE, or WORKER")
    status: Optional[str] = Field(None, description="ONLINE, DEGRADED, OFFLINE, or MAINTENANCE")
    cpu_usage_pct: Optional[Decimal] = Field(None, ge=0, le=100)
    memory_usage_pct: Optional[Decimal] = Field(None, ge=0, le=100)


class SystemServerOutSchema(BaseModel):
    id: int
    name: str
    ip_address: str
    server_type: str
    status: str
    cpu_usage_pct: Decimal
    memory_usage_pct: Decimal
    last_ping: datetime

    class Config:
        from_attributes = True


# =====================================================================
# 2. API KEY SCHEMAS
# =====================================================================

class APIKeyCreateSchema(BaseModel):
    user_id: int = Field(..., description="Target User ID owning the API key")
    key_name: str = Field(..., max_length=100, example="Algorithmic Trading Bot Key")
    rate_limit_per_minute: int = Field(60, ge=1, example=120)
    expires_at: Optional[datetime] = Field(None, example="2027-09-24T00:00:00Z")


class APIKeyUpdateSchema(BaseModel):
    key_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = Field(None)
    rate_limit_per_minute: Optional[int] = Field(None, ge=1)
    expires_at: Optional[datetime] = Field(None)


class APIKeyOutSchema(BaseModel):
    id: int
    user_id: int
    key_name: str
    api_key: str
    is_active: bool
    rate_limit_per_minute: int
    created_at: datetime
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


# =====================================================================
# 3. ASYNC TASK LOG SCHEMAS
# =====================================================================

class AsyncTaskLogCreateSchema(BaseModel):
    task_id: str = Field(..., max_length=255, example="celery-task-uuid-99812")
    task_name: str = Field(..., max_length=255, example="portfolio.tasks.calculate_daily_nav")
    status: str = Field("PENDING", example="PENDING", description="PENDING, STARTED, SUCCESS, FAILURE, or RETRY")
    runtime_seconds: Optional[Decimal] = Field(None, ge=0, example="1.4520")
    traceback: Optional[str] = Field(None, example="")
    completed_at: Optional[datetime] = Field(None)


class AsyncTaskLogUpdateSchema(BaseModel):
    status: Optional[str] = Field(None, description="PENDING, STARTED, SUCCESS, FAILURE, or RETRY")
    runtime_seconds: Optional[Decimal] = Field(None, ge=0)
    traceback: Optional[str] = Field(None)
    completed_at: Optional[datetime] = Field(None)


class AsyncTaskLogOutSchema(BaseModel):
    id: int
    task_id: str
    task_name: str
    status: str
    runtime_seconds: Optional[Decimal]
    traceback: str
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# =====================================================================
# 4. SYSTEM SETTING SCHEMAS
# =====================================================================

class SystemSettingCreateSchema(BaseModel):
    key: str = Field(..., max_length=100, example="MAINTENANCE_MODE")
    value: str = Field(..., example="false")
    description: Optional[str] = Field(None, example="Globally disables trading when set to true.")
    is_encrypted: bool = Field(False)


class SystemSettingUpdateSchema(BaseModel):
    value: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    is_encrypted: Optional[bool] = Field(None)


class SystemSettingOutSchema(BaseModel):
    id: int
    key: str
    value: str
    description: Optional[str]
    is_encrypted: bool
    updated_at: datetime

    class Config:
        from_attributes = True


# =====================================================================
# 5. SYSTEM INCIDENT SCHEMAS
# =====================================================================

class SystemIncidentCreateSchema(BaseModel):
    server_id: Optional[int] = Field(None, description="Related Server ID if applicable")
    title: str = Field(..., max_length=255, example="Redis Connection Pool Exhaustion")
    description: str = Field(..., example="High concurrency calls dropped connections to the Redis broker node.")
    severity: str = Field("MEDIUM", example="HIGH", description="LOW, MEDIUM, HIGH, or CRITICAL")
    status: str = Field("OPEN", example="OPEN", description="OPEN, INVESTIGATING, IDENTIFIED, or RESOLVED")


class SystemIncidentUpdateSchema(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None)
    severity: Optional[str] = Field(None, description="LOW, MEDIUM, HIGH, or CRITICAL")
    status: Optional[str] = Field(None, description="OPEN, INVESTIGATING, IDENTIFIED, or RESOLVED")
    resolved_at: Optional[datetime] = Field(None)


class SystemIncidentOutSchema(BaseModel):
    id: int
    server_id: Optional[int]
    title: str
    description: str
    severity: str
    status: str
    reported_by_id: Optional[int]
    created_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True