# config/api.py
from typing import List, Optional
from ninja import Query, File, UploadedFile

from .router import router
from .schemas import (
    ClientProfileCreateSchema, ClientProfileUpdateSchema, ClientProfileOutSchema,
    KYCDocumentCreateSchema, KYCDocumentUpdateSchema, KYCDocumentOutSchema,
    InteractionLogCreateSchema, InteractionLogOutSchema,
    LeadPipelineCreateSchema, LeadPipelineUpdateSchema, LeadPipelineOutSchema
)
from .service import ClientRelationsService

# --- Client Profiles ---
@router.post("/profiles/", response={201: ClientProfileOutSchema})
def create_client_profile(request, payload: ClientProfileCreateSchema):
    return 201, ClientRelationsService.create_client_profile(data=payload)

@router.get("/profiles/", response=List[ClientProfileOutSchema])
def list_client_profiles(request):
    return ClientRelationsService.list_client_profiles()

@router.patch("/profiles/{profile_id}/", response=ClientProfileOutSchema)
def update_client_profile(request, profile_id: int, payload: ClientProfileUpdateSchema):
    return ClientRelationsService.update_client_profile(profile_id=profile_id, data=payload)

# --- KYC Documents ---
@router.post("/kyc/", response={201: KYCDocumentOutSchema})
def create_kyc_document(request, payload: KYCDocumentCreateSchema = Query(...), file: UploadedFile = File(...)):
    return 201, ClientRelationsService.create_kyc_document(data=payload, file=file)

@router.get("/kyc/", response=List[KYCDocumentOutSchema])
def list_kyc_documents(request, client_id: Optional[int] = Query(None)):
    return ClientRelationsService.list_kyc_documents(client_id=client_id)

@router.patch("/kyc/{doc_id}/", response=KYCDocumentOutSchema)
def update_kyc_document(request, doc_id: int, payload: KYCDocumentUpdateSchema):
    return ClientRelationsService.update_kyc_document(doc_id=doc_id, data=payload)

# --- Interaction Logs ---
@router.post("/interactions/", response={201: InteractionLogOutSchema})
def create_interaction_log(request, payload: InteractionLogCreateSchema):
    return 201, ClientRelationsService.create_interaction_log(staff=request.user, data=payload)

@router.get("/interactions/", response=List[InteractionLogOutSchema])
def list_interaction_logs(request, client_id: Optional[int] = Query(None)):
    return ClientRelationsService.list_interaction_logs(client_id=client_id)

# --- Lead Pipeline ---
@router.post("/leads/", response={201: LeadPipelineOutSchema})
def create_lead(request, payload: LeadPipelineCreateSchema):
    return 201, ClientRelationsService.create_lead(data=payload)

@router.get("/leads/", response=List[LeadPipelineOutSchema])
def list_leads(request, stage: Optional[str] = Query(None)):
    return ClientRelationsService.list_leads(stage=stage)

@router.patch("/leads/{lead_id}/", response=LeadPipelineOutSchema)
def update_lead(request, lead_id: int, payload: LeadPipelineUpdateSchema):
    return ClientRelationsService.update_lead(lead_id=lead_id, data=payload)