from typing import List, Optional
from django.shortcuts import get_object_or_404
from ninja import Query

from .router import router
from .models import (
    ClearingHouse,
    ClearingMemberAccount,
    TradeSettlement,
    MarginRequirement,
    SettlementReconciliation,
)
from .schemas import (
    ClearingHouseCreateSchema,
    ClearingHouseUpdateSchema,
    ClearingHouseOutSchema,
    ClearingMemberAccountCreateSchema,
    ClearingMemberAccountUpdateSchema,
    ClearingMemberAccountOutSchema,
    TradeSettlementCreateSchema,
    TradeSettlementUpdateSchema,
    TradeSettlementOutSchema,
    MarginRequirementCreateSchema,
    MarginRequirementUpdateSchema,
    MarginRequirementOutSchema,
    SettlementReconciliationCreateSchema,
    SettlementReconciliationUpdateSchema,
    SettlementReconciliationOutSchema,
)
from .service import OperationsClearingService


# =====================================================================
# 1. CLEARING HOUSE ENDPOINTS
# =====================================================================

@router.post("/houses/", response={201: ClearingHouseOutSchema})
def create_clearing_house(request, payload: ClearingHouseCreateSchema):
    return 201, OperationsClearingService.create_clearing_house(data=payload)

@router.get("/houses/", response=List[ClearingHouseOutSchema])
def list_clearing_houses(request, is_active: Optional[bool] = Query(None)):
    return OperationsClearingService.list_clearing_houses(is_active=is_active)

@router.get("/houses/{house_id}/", response=ClearingHouseOutSchema)
def get_clearing_house(request, house_id: int):
    return get_object_or_404(ClearingHouse, id=house_id)

@router.patch("/houses/{house_id}/", response=ClearingHouseOutSchema)
def update_clearing_house(request, house_id: int, payload: ClearingHouseUpdateSchema):
    return OperationsClearingService.update_clearing_house(house_id=house_id, data=payload)


# =====================================================================
# 2. CLEARING MEMBER ACCOUNT ENDPOINTS
# =====================================================================

@router.post("/accounts/", response={201: ClearingMemberAccountOutSchema})
def create_member_account(request, payload: ClearingMemberAccountCreateSchema):
    return 201, OperationsClearingService.create_member_account(data=payload)

@router.get("/accounts/", response=List[ClearingMemberAccountOutSchema])
def list_member_accounts(request, clearing_house_id: Optional[int] = Query(None), is_active: Optional[bool] = Query(None)):
    return OperationsClearingService.list_member_accounts(clearing_house_id=clearing_house_id, is_active=is_active)

@router.get("/accounts/{account_id}/", response=ClearingMemberAccountOutSchema)
def get_member_account(request, account_id: int):
    return get_object_or_404(ClearingMemberAccount, id=account_id)

@router.patch("/accounts/{account_id}/", response=ClearingMemberAccountOutSchema)
def update_member_account(request, account_id: int, payload: ClearingMemberAccountUpdateSchema):
    return OperationsClearingService.update_member_account(account_id=account_id, data=payload)


# =====================================================================
# 3. TRADE SETTLEMENT ENDPOINTS
# =====================================================================

@router.post("/settlements/", response={201: TradeSettlementOutSchema})
def create_trade_settlement(request, payload: TradeSettlementCreateSchema):
    return 201, OperationsClearingService.create_trade_settlement(staff_user=request.user, data=payload)

@router.get("/settlements/", response=List[TradeSettlementOutSchema])
def list_trade_settlements(request, status: Optional[str] = Query(None), settlement_type: Optional[str] = Query(None), symbol: Optional[str] = Query(None)):
    return OperationsClearingService.list_trade_settlements(status=status, settlement_type=settlement_type, symbol=symbol)

@router.get("/settlements/{settlement_id}/", response=TradeSettlementOutSchema)
def get_trade_settlement(request, settlement_id: int):
    return get_object_or_404(TradeSettlement.objects.select_related("clearing_house", "clearing_account", "user"), id=settlement_id)

@router.patch("/settlements/{settlement_id}/", response=TradeSettlementOutSchema)
def update_trade_settlement(request, settlement_id: int, payload: TradeSettlementUpdateSchema):
    return OperationsClearingService.update_trade_settlement(settlement_id=settlement_id, data=payload)


# =====================================================================
# 4. MARGIN REQUIREMENT ENDPOINTS
# =====================================================================

@router.post("/margins/", response={201: MarginRequirementOutSchema})
def create_margin_requirement(request, payload: MarginRequirementCreateSchema):
    return 201, OperationsClearingService.create_margin_requirement(data=payload)

@router.get("/margins/", response=List[MarginRequirementOutSchema])
def list_margin_requirements(request, is_margin_call_active: Optional[bool] = Query(None)):
    return OperationsClearingService.list_margin_requirements(is_margin_call_active=is_margin_call_active)

@router.get("/margins/{margin_id}/", response=MarginRequirementOutSchema)
def get_margin_requirement(request, margin_id: int):
    return get_object_or_404(MarginRequirement.objects.select_related("clearing_account"), id=margin_id)

@router.patch("/margins/{margin_id}/", response=MarginRequirementOutSchema)
def update_margin_requirement(request, margin_id: int, payload: MarginRequirementUpdateSchema):
    return OperationsClearingService.update_margin_requirement(margin_id=margin_id, data=payload)


# =====================================================================
# 5. SETTLEMENT RECONCILIATION ENDPOINTS
# =====================================================================

@router.post("/reconciliations/", response={201: SettlementReconciliationOutSchema})
def create_reconciliation_break(request, payload: SettlementReconciliationCreateSchema):
    return 201, OperationsClearingService.create_reconciliation_break(data=payload)

@router.get("/reconciliations/", response=List[SettlementReconciliationOutSchema])
def list_reconciliation_breaks(request, status: Optional[str] = Query(None), break_type: Optional[str] = Query(None)):
    return OperationsClearingService.list_reconciliation_breaks(status=status, break_type=break_type)

@router.get("/reconciliations/{break_id}/", response=SettlementReconciliationOutSchema)
def get_reconciliation_break(request, break_id: int):
    return get_object_or_404(SettlementReconciliation.objects.select_related("settlement", "resolved_by"), id=break_id)

@router.patch("/reconciliations/{break_id}/", response=SettlementReconciliationOutSchema)
def update_reconciliation_break(request, break_id: int, payload: SettlementReconciliationUpdateSchema):
    return OperationsClearingService.update_reconciliation_break(break_id=break_id, staff_user=request.user, data=payload)