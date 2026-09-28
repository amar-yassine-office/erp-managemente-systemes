from typing import List, Optional
from django.shortcuts import get_object_or_404
from ninja import Query

from .router import router
from .models import (
    AssetAllocation,
    Portfolio,
    PortfolioPosition,
    PortfolioPerformance,
)
from .schemas import (
    AssetAllocationCreateSchema,
    AssetAllocationUpdateSchema,
    AssetAllocationOutSchema,
    PortfolioCreateSchema,
    PortfolioUpdateSchema,
    PortfolioOutSchema,
    PortfolioPositionCreateSchema,
    PortfolioPositionUpdateSchema,
    PortfolioPositionOutSchema,
    PortfolioPerformanceCreateSchema,
    PortfolioPerformanceUpdateSchema,
    PortfolioPerformanceOutSchema,
)
from .service import PortfolioManagementService

# =====================================================================
# 1. ASSET ALLOCATION ENDPOINTS
# =====================================================================

@router.post("/allocations/", response={201: AssetAllocationOutSchema})
def create_asset_allocation(request, payload: AssetAllocationCreateSchema):
    return 201, PortfolioManagementService.create_asset_allocation(data=payload)

@router.get("/allocations/", response=List[AssetAllocationOutSchema])
def list_asset_allocations(request):
    return PortfolioManagementService.list_asset_allocations()

@router.get("/allocations/{allocation_id}/", response=AssetAllocationOutSchema)
def get_asset_allocation(request, allocation_id: int):
    return get_object_or_404(AssetAllocation, id=allocation_id)

@router.patch("/allocations/{allocation_id}/", response=AssetAllocationOutSchema)
def update_asset_allocation(request, allocation_id: int, payload: AssetAllocationUpdateSchema):
    return PortfolioManagementService.update_asset_allocation(allocation_id=allocation_id, data=payload)


# =====================================================================
# 2. PORTFOLIO ENDPOINTS
# =====================================================================

@router.post("/portfolios/", response={201: PortfolioOutSchema})
def create_portfolio(request, payload: PortfolioCreateSchema):
    return 201, PortfolioManagementService.create_portfolio(user=request.user, data=payload)

@router.get("/portfolios/", response=List[PortfolioOutSchema])
def list_portfolios(request, user_id: Optional[int] = Query(None), status: Optional[str] = Query(None)):
    return PortfolioManagementService.list_portfolios(user_id=user_id, status=status)

@router.get("/portfolios/{portfolio_id}/", response=PortfolioOutSchema)
def get_portfolio(request, portfolio_id: int):
    return get_object_or_404(Portfolio.objects.select_related("user", "strategy"), id=portfolio_id)

@router.patch("/portfolios/{portfolio_id}/", response=PortfolioOutSchema)
def update_portfolio(request, portfolio_id: int, payload: PortfolioUpdateSchema):
    return PortfolioManagementService.update_portfolio(portfolio_id=portfolio_id, data=payload)


# =====================================================================
# 3. PORTFOLIO POSITION ENDPOINTS
# =====================================================================

@router.post("/positions/", response={201: PortfolioPositionOutSchema})
def create_position(request, payload: PortfolioPositionCreateSchema):
    return 201, PortfolioManagementService.create_position(data=payload)

@router.get("/positions/", response=List[PortfolioPositionOutSchema])
def list_positions(request, portfolio_id: Optional[int] = Query(None), symbol: Optional[str] = Query(None)):
    return PortfolioManagementService.list_positions(portfolio_id=portfolio_id, symbol=symbol)

@router.get("/positions/{position_id}/", response=PortfolioPositionOutSchema)
def get_position(request, position_id: int):
    return get_object_or_404(PortfolioPosition.objects.select_related("portfolio"), id=position_id)

@router.patch("/positions/{position_id}/", response=PortfolioPositionOutSchema)
def update_position(request, position_id: int, payload: PortfolioPositionUpdateSchema):
    return PortfolioManagementService.update_position(position_id=position_id, data=payload)


# =====================================================================
# 4. PORTFOLIO PERFORMANCE ENDPOINTS
# =====================================================================

@router.post("/performance/", response={201: PortfolioPerformanceOutSchema})
def record_performance(request, payload: PortfolioPerformanceCreateSchema):
    return 201, PortfolioManagementService.record_performance(data=payload)

@router.get("/performance/", response=List[PortfolioPerformanceOutSchema])
def list_performance_records(request, portfolio_id: Optional[int] = Query(None)):
    return PortfolioManagementService.list_performance_records(portfolio_id=portfolio_id)