from ninja import NinjaAPI

# إنشاء كائن الـ API مع إعطائه عنواناً ووصفاً
api = NinjaAPI(
    title="ERP Finance & Stock API",
    version="1.0.0",
    description="الدليل التفاعلي لجميع مسارات الـ API الخاصة بالنظام",
)

# اختبار مسار بسيط (Endpoint)
@api.get("/status")
def status(request):
    return {"status": "ok", "message": "Django Ninja API is running successfully"}




#
# config/api.py
from ninja_extra import NinjaExtraAPI  # Use NinjaExtraAPI instead of NinjaAPI
from ninja_jwt.controller import NinjaJWTDefaultController

api = NinjaExtraAPI(
    title="Client Asset & Equity Management ERP API",
    version="1.0.0",
    description="Enterprise ERP API for asset management, financial ledger, and IT operations.",
    docs_url="/docs",
)

# Now register_controllers will work seamlessly:
api.register_controllers(NinjaJWTDefaultController)

from ComplianceLegal.api import router as compliance_router


from ComplianceLegal.api import router as compliance_router

# Mount it to your main API instance
api.add_router("/compliance/", compliance_router)

from ITSystems.router import router as it_systems_router

api.add_router("/it-systems/", it_systems_router)

from OperationsClearing.router import router as operations_clearing_router

api.add_router("/operations-clearing/", operations_clearing_router)

from PortfolioManagement.api import router as portfolio_router
api.add_router("/portfolios/", portfolio_router)

from ResearchAnalytics.api import router as research_router
api.add_router("/research/", research_router)

# for the latest section 

from RiskManagement.api import router as risk_management_router

api.add_router("/risk/", risk_management_router)

# the first one 
from AccountingFinance.api import router as accounting_router
api.add_router("/accounting/", accounting_router)

# this is for the second one 
from ClientRelations.api import router as client_relations_router
api.add_router("/clients/", client_relations_router)