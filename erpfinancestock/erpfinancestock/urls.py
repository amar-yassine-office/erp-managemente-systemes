"""
URL configuration for erpfinancestock project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView
from .api import api
from erpfinancestock.api import api

admin.site.site_header = "ERP Finance System"  # Replaces 'Django administration'
admin.site.site_title = "ERP System for Managing the Company"  # Browser tab title
admin.site.index_title = "The Management System"  # Dashboard main heading



urlpatterns = [
    path('', RedirectView.as_view(url='api/docs', permanent=False)),
    
    path('admin/', admin.site.urls),
    path('api/', api.urls),
    
     
]
# config/api.py (or your central api.py)
from django.core.exceptions import ValidationError
from ninja_extra import NinjaExtraAPI
from ninja_jwt.controller import NinjaJWTDefaultController

# Import the router from your ComplianceLegal app
from ComplianceLegal.api import router as compliance_router  # or ComplianceLegal.router if using router.py

api = NinjaExtraAPI(
    title="Client Asset & Equity Management ERP API",
    version="1.0.0",
    docs_url="/docs",
)

api.register_controllers(NinjaJWTDefaultController)

# THIS IS CRITICAL: This line makes the CRUD operations appear in Swagger!
api.add_router("/compliance/", compliance_router)