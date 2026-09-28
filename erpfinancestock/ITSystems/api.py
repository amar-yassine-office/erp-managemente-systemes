from typing import List, Optional
from django.shortcuts import get_object_or_404
from ninja import Query

from .router import router
from .models import (
    SystemServer,
    APIKey,
    AsyncTaskLog,
    SystemSetting,
    SystemIncident,
)
from .schemas import (
    SystemServerCreateSchema,
    SystemServerUpdateSchema,
    SystemServerOutSchema,
    APIKeyCreateSchema,
    APIKeyUpdateSchema,
    APIKeyOutSchema,
    AsyncTaskLogCreateSchema,
    AsyncTaskLogUpdateSchema,
    AsyncTaskLogOutSchema,
    SystemSettingCreateSchema,
    SystemSettingUpdateSchema,
    SystemSettingOutSchema,
    SystemIncidentCreateSchema,
    SystemIncidentUpdateSchema,
    SystemIncidentOutSchema,
)
from .service import ITSystemsService


# =====================================================================
# 1. SYSTEM SERVER ENDPOINTS
# =====================================================================

@router.post("/servers/", response={201: SystemServerOutSchema})
def create_server(request, payload: SystemServerCreateSchema):
    return 201, ITSystemsService.create_server(staff_user=request.user, data=payload)

@router.get("/servers/", response=List[SystemServerOutSchema])
def list_servers(request, server_type: Optional[str] = Query(None), status: Optional[str] = Query(None)):
    return ITSystemsService.list_servers(server_type=server_type, status=status)

@router.get("/servers/{server_id}/", response=SystemServerOutSchema)
def get_server(request, server_id: int):
    return get_object_or_404(SystemServer, id=server_id)

@router.patch("/servers/{server_id}/", response=SystemServerOutSchema)
def update_server(request, server_id: int, payload: SystemServerUpdateSchema):
    return ITSystemsService.update_server(server_id=server_id, staff_user=request.user, data=payload)


# =====================================================================
# 2. API KEY MANAGEMENT ENDPOINTS
# =====================================================================

@router.post("/api-keys/", response={201: APIKeyOutSchema})
def generate_api_key(request, payload: APIKeyCreateSchema):
    return 201, ITSystemsService.generate_api_key(staff_user=request.user, data=payload)

@router.get("/api-keys/", response=List[APIKeyOutSchema])
def list_api_keys(request, user_id: Optional[int] = Query(None), is_active: Optional[bool] = Query(None)):
    return ITSystemsService.list_api_keys(user_id=user_id, is_active=is_active)

@router.patch("/api-keys/{key_id}/", response=APIKeyOutSchema)
def update_api_key(request, key_id: int, payload: APIKeyUpdateSchema):
    return ITSystemsService.update_api_key(key_id=key_id, staff_user=request.user, data=payload)


# =====================================================================
# 3. ASYNC TASK LOG ENDPOINTS
# =====================================================================

@router.post("/task-logs/", response={201: AsyncTaskLogOutSchema})
def create_task_log(request, payload: AsyncTaskLogCreateSchema):
    return 201, ITSystemsService.create_task_log(data=payload)

@router.get("/task-logs/", response=List[AsyncTaskLogOutSchema])
def list_task_logs(request, status: Optional[str] = Query(None), task_name: Optional[str] = Query(None)):
    return ITSystemsService.list_task_logs(status=status, task_name=task_name)

@router.patch("/task-logs/{task_id_str}/", response=AsyncTaskLogOutSchema)
def update_task_log(request, task_id_str: str, payload: AsyncTaskLogUpdateSchema):
    return ITSystemsService.update_task_log(task_id_str=task_id_str, data=payload)


# =====================================================================
# 4. SYSTEM SETTING ENDPOINTS
# =====================================================================

@router.post("/settings/", response={201: SystemSettingOutSchema})
def set_system_setting(request, payload: SystemSettingCreateSchema):
    return 201, ITSystemsService.set_system_setting(staff_user=request.user, data=payload)

@router.get("/settings/", response=List[SystemSettingOutSchema])
def list_system_settings(request):
    return ITSystemsService.list_system_settings()

@router.get("/settings/{key}/", response=SystemSettingOutSchema)
def get_system_setting(request, key: str):
    return get_object_or_404(SystemSetting, key=key)


# =====================================================================
# 5. SYSTEM INCIDENT ENDPOINTS
# =====================================================================

@router.post("/incidents/", response={201: SystemIncidentOutSchema})
def create_incident(request, payload: SystemIncidentCreateSchema):
    return 201, ITSystemsService.create_incident(staff_user=request.user, data=payload)

@router.get("/incidents/", response=List[SystemIncidentOutSchema])
def list_incidents(request, severity: Optional[str] = Query(None), status: Optional[str] = Query(None)):
    return ITSystemsService.list_incidents(severity=severity, status=status)

@router.get("/incidents/{incident_id}/", response=SystemIncidentOutSchema)
def get_incident(request, incident_id: int):
    return get_object_or_404(SystemIncident.objects.select_related("server", "reported_by"), id=incident_id)

@router.patch("/incidents/{incident_id}/", response=SystemIncidentOutSchema)
def update_incident(request, incident_id: int, payload: SystemIncidentUpdateSchema):
    return ITSystemsService.update_incident(incident_id=incident_id, staff_user=request.user, data=payload)