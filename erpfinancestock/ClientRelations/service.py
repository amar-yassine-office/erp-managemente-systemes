
from typing import List, Optional
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from ninja import UploadedFile

from .models import ClientProfile, KYCDocument, InteractionLog, LeadPipeline
from .schemas import (
    ClientProfileCreateSchema, ClientProfileUpdateSchema,
    KYCDocumentCreateSchema, KYCDocumentUpdateSchema,
    InteractionLogCreateSchema,
    LeadPipelineCreateSchema, LeadPipelineUpdateSchema
)

User = get_user_model()


class ClientRelationsService:

    # --- Client Profile ---
    @classmethod
    @transaction.atomic
    def create_client_profile(cls, data: ClientProfileCreateSchema) -> ClientProfile:
        payload = data.dict()
        user_id = payload.pop("user_id")
        mgr_id = payload.pop("relationship_manager_id", None)
        
        user = get_object_or_404(User, id=user_id)
        manager = get_object_or_404(User, id=mgr_id) if mgr_id else None
        
        return ClientProfile.objects.create(
            user=user,
            relationship_manager=manager,
            **payload
        )

    @staticmethod
    def list_client_profiles() -> List[ClientProfile]:
        return ClientProfile.objects.select_related("user", "relationship_manager").all()

    @classmethod
    @transaction.atomic
    def update_client_profile(cls, profile_id: int, data: ClientProfileUpdateSchema) -> ClientProfile:
        profile = get_object_or_404(ClientProfile, id=profile_id)
        payload = data.dict(exclude_unset=True)
        if "relationship_manager_id" in payload:
            mgr_id = payload.pop("relationship_manager_id")
            profile.relationship_manager = get_object_or_404(User, id=mgr_id) if mgr_id else None
        for k, v in payload.items():
            setattr(profile, k, v)
        profile.save()
        return profile

    # --- KYC Document ---
    @classmethod
    @transaction.atomic
    def create_kyc_document(cls, data: KYCDocumentCreateSchema, file: UploadedFile) -> KYCDocument:
        client = get_object_or_404(ClientProfile, id=data.client_id)
        return KYCDocument.objects.create(
            client=client,
            document_type=data.document_type,
            document_number=data.document_number,
            file=file,
            expiry_date=data.expiry_date
        )

    @staticmethod
    def list_kyc_documents(client_id: Optional[int] = None) -> List[KYCDocument]:
        qs = KYCDocument.objects.select_related("client__user").all()
        if client_id:
            qs = qs.filter(client_id=client_id)
        return qs

    @classmethod
    @transaction.atomic
    def update_kyc_document(cls, doc_id: int, data: KYCDocumentUpdateSchema) -> KYCDocument:
        doc = get_object_or_404(KYCDocument, id=doc_id)
        payload = data.dict(exclude_unset=True)
        if "status" in payload and payload["status"] == 'APPROVED' and doc.status != 'APPROVED':
            doc.verified_at = timezone.now()
        for k, v in payload.items():
            setattr(doc, k, v)
        doc.save()
        return doc

    # --- Interaction Log ---
    @classmethod
    @transaction.atomic
    def create_interaction_log(cls, staff: User, data: InteractionLogCreateSchema) -> InteractionLog:
        client = get_object_or_404(ClientProfile, id=data.client_id)
        payload = data.dict()
        payload.pop("client_id")
        return InteractionLog.objects.create(
            client=client,
            staff_member=staff,
            **payload
        )

    @staticmethod
    def list_interaction_logs(client_id: Optional[int] = None) -> List[InteractionLog]:
        qs = InteractionLog.objects.select_related("client__user", "staff_member").all()
        if client_id:
            qs = qs.filter(client_id=client_id)
        return qs

    # --- Lead Pipeline ---
    @classmethod
    @transaction.atomic
    def create_lead(cls, data: LeadPipelineCreateSchema) -> LeadPipeline:
        payload = data.dict()
        assigned_id = payload.pop("assigned_to_id", None)
        assigned_to = get_object_or_404(User, id=assigned_id) if assigned_id else None
        return LeadPipeline.objects.create(assigned_to=assigned_to, **payload)

    @staticmethod
    def list_leads(stage: Optional[str] = None) -> List[LeadPipeline]:
        qs = LeadPipeline.objects.select_related("assigned_to").all()
        if stage:
            qs = qs.filter(stage=stage)
        return qs

    @classmethod
    @transaction.atomic
    def update_lead(cls, lead_id: int, data: LeadPipelineUpdateSchema) -> LeadPipeline:
        lead = get_object_or_404(LeadPipeline, id=lead_id)
        payload = data.dict(exclude_unset=True)
        if "assigned_to_id" in payload:
            assigned_id = payload.pop("assigned_to_id")
            lead.assigned_to = get_object_or_404(User, id=assigned_id) if assigned_id else None
        for k, v in payload.items():
            setattr(lead, k, v)
        lead.save()
        return lead
    