from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import ClientProfile, InteractionLog, KYCDocument, LeadPipeline


class KYCDocumentInline(admin.TabularInline):
    model = KYCDocument
    extra = 0
    fields = ('document_type', 'document_number', 'status', 'expiry_date', 'file')


class InteractionLogInline(admin.TabularInline):
    model = InteractionLog
    extra = 0
    fields = ('channel', 'subject', 'staff_member', 'follow_up_required', 'follow_up_date', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'client_type',
        'risk_tolerance',
        'relationship_manager',
        'net_worth_estimate',
        'created_at',
    )
    list_filter = ('client_type', 'risk_tolerance', 'created_at')
    search_fields = (
        'user__username',
        'user__first_name',
        'user__last_name',
        'user__email',
        'tax_id',
    )
    inlines = [KYCDocumentInline, InteractionLogInline]

    fieldsets = (
        ('User Association', {'fields': ('user', 'relationship_manager')}),
        ('Classification & Info', {'fields': ('client_type', 'phone_number', 'tax_id', 'address')}),
        ('Investment Profile', {'fields': ('risk_tolerance', 'net_worth_estimate', 'investment_goal')}),
    )


@admin.register(KYCDocument)
class KYCDocumentAdmin(admin.ModelAdmin):
    list_display = (
        'client',
        'document_type',
        'document_number',
        'status',
        'expiry_date',
        'uploaded_at',
    )
    list_filter = ('status', 'document_type', 'uploaded_at')
    search_fields = ('client__user__username', 'document_number')


@admin.register(InteractionLog)
class InteractionLogAdmin(admin.ModelAdmin):
    list_display = (
        'client',
        'subject',
        'channel',
        'staff_member',
        'follow_up_required',
        'follow_up_date',
        'created_at',
    )
    list_filter = ('channel', 'follow_up_required', 'created_at')
    search_fields = ('client__user__username', 'subject', 'summary')


@admin.register(LeadPipeline)
class LeadPipelineAdmin(admin.ModelAdmin):
    list_display = (
        'full_name',
        'company_name',
        'stage',
        'estimated_investment_amount',
        'assigned_to',
        'created_at',
    )
    list_filter = ('stage', 'created_at')
    search_fields = ('full_name', 'email', 'company_name')
    