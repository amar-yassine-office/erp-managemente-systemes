from typing import List, Optional
from django.shortcuts import get_object_or_404
from ninja import Router, Query
from ninja_jwt.authentication import JWTAuth
from ninja_jwt.authentication import JWTAuth

router = Router(auth=JWTAuth())

from .models import (
    ComplianceCheck,
    RestrictedAsset,
    SuspiciousActivityReport,
    TradeSurveillanceRule,
    AuditLog,
)
from .schemas import (
    ComplianceCheckCreateSchema,
    ComplianceCheckUpdateSchema,
    ComplianceCheckOutSchema,
    RestrictedAssetCreateSchema,
    RestrictedAssetUpdateSchema,
    RestrictedAssetOutSchema,
    SuspiciousActivityReportCreateSchema,
    SuspiciousActivityReportUpdateSchema,
    SuspiciousActivityReportOutSchema,
    TradeSurveillanceRuleCreateSchema,
    TradeSurveillanceRuleUpdateSchema,
    TradeSurveillanceRuleOutSchema,
    AuditLogOutSchema,
)
from .service import ComplianceLegalService

router = Router(tags=["Compliance & Legal"], auth=JWTAuth())

# Compliance Check Endpoints
@router.post("/checks/", response={201: ComplianceCheckOutSchema})
def create_compliance_check(request, payload: ComplianceCheckCreateSchema):
    return 201, ComplianceLegalService.create_compliance_check(staff_user=request.user, data=payload)

@router.get("/checks/", response=List[ComplianceCheckOutSchema])
def list_compliance_checks(request, user_id: Optional[int] = Query(None), check_type: Optional[str] = Query(None), status: Optional[str] = Query(None)):
    return ComplianceLegalService.list_compliance_checks(user_id=user_id, check_type=check_type, status=status)

@router.get("/checks/{check_id}/", response=ComplianceCheckOutSchema)
def get_compliance_check(request, check_id: int):
    return get_object_or_404(ComplianceCheck.objects.select_related("user", "performed_by"), id=check_id)

@router.patch("/checks/{check_id}/", response=ComplianceCheckOutSchema)
def update_compliance_check(request, check_id: int, payload: ComplianceCheckUpdateSchema):
    return ComplianceLegalService.update_compliance_check(check_id=check_id, staff_user=request.user, data=payload)

# Restricted Asset Endpoints
@router.post("/restricted-assets/", response={201: RestrictedAssetOutSchema})
def add_restricted_asset(request, payload: RestrictedAssetCreateSchema):
    return 201, ComplianceLegalService.add_restricted_asset(staff_user=request.user, data=payload)

@router.get("/restricted-assets/", response=List[RestrictedAssetOutSchema])
def list_restricted_assets(request, is_active_only: bool = Query(True)):
    return ComplianceLegalService.list_restricted_assets(is_active_only=is_active_only)

@router.patch("/restricted-assets/{asset_id}/", response=RestrictedAssetOutSchema)
def update_restricted_asset(request, asset_id: int, payload: RestrictedAssetUpdateSchema):
    return ComplianceLegalService.update_restricted_asset(asset_id=asset_id, staff_user=request.user, data=payload)

# SAR Endpoints
@router.post("/sars/", response={201: SuspiciousActivityReportOutSchema})
def raise_sar(request, payload: SuspiciousActivityReportCreateSchema):
    return 201, ComplianceLegalService.raise_sar(staff_user=request.user, data=payload)

@router.get("/sars/", response=List[SuspiciousActivityReportOutSchema])
def list_sars(request, severity: Optional[str] = Query(None), status: Optional[str] = Query(None)):
    return ComplianceLegalService.list_sars(severity=severity, status=status)

@router.get("/sars/{report_id}/", response=SuspiciousActivityReportOutSchema)
def get_sar(request, report_id: int):
    return get_object_or_404(SuspiciousActivityReport.objects.select_related("user", "investigated_by"), id=report_id)

@router.patch("/sars/{report_id}/", response=SuspiciousActivityReportOutSchema)
def update_sar_status(request, report_id: int, payload: SuspiciousActivityReportUpdateSchema):
    return ComplianceLegalService.update_sar_status(report_id=report_id, staff_user=request.user, data=payload)

# Surveillance Rule Endpoints
@router.post("/surveillance-rules/", response={201: TradeSurveillanceRuleOutSchema})
def create_surveillance_rule(request, payload: TradeSurveillanceRuleCreateSchema):
    return 201, ComplianceLegalService.create_surveillance_rule(staff_user=request.user, data=payload)

@router.get("/surveillance-rules/", response=List[TradeSurveillanceRuleOutSchema])
def list_surveillance_rules(request):
    return TradeSurveillanceRule.objects.all()

@router.patch("/surveillance-rules/{rule_id}/", response=TradeSurveillanceRuleOutSchema)
def update_surveillance_rule(request, rule_id: int, payload: TradeSurveillanceRuleUpdateSchema):
    return ComplianceLegalService.update_surveillance_rule(rule_id=rule_id, staff_user=request.user, data=payload)

# Audit Log Endpoints
@router.get("/audit-logs/", response=List[AuditLogOutSchema])
def list_audit_logs(request, actor_id: Optional[int] = Query(None), action_type: Optional[str] = Query(None)):
    return ComplianceLegalService.list_audit_logs(actor_id=actor_id, action_type=action_type)

@router.get("/audit-logs/{log_id}/", response=AuditLogOutSchema)
def get_audit_log(request, log_id: int):
    return get_object_or_404(AuditLog.objects.select_related("actor"), id=log_id)