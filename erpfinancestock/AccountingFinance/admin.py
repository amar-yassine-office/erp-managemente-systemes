from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import (
    Account,
    FiscalYear,
    Invoice,
    InvoiceItem,
    JournalEntry,
    JournalEntryItem,
    Payment,
    TaxRate,
)


@admin.register(FiscalYear)
class FiscalYearAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_closed')
    list_filter = ('is_closed',)


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'account_type', 'parent', 'is_active')
    list_filter = ('account_type', 'is_active')
    search_fields = ('code', 'name')


class JournalEntryItemInline(admin.TabularInline):
    model = JournalEntryItem
    extra = 2


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ('entry_number', 'date', 'fiscal_year', 'status', 'created_by', 'posted_by')
    list_filter = ('status', 'fiscal_year', 'date')
    search_fields = ('entry_number', 'description')
    inlines = [JournalEntryItemInline]


@admin.register(TaxRate)
class TaxRateAdmin(admin.ModelAdmin):
    list_display = ('name', 'rate', 'account', 'is_active')
    list_filter = ('is_active',)


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        'invoice_number',
        'invoice_type',
        'user',
        'issue_date',
        'due_date',
        'total_amount',
        'status',
    )
    list_filter = ('invoice_type', 'status', 'issue_date')
    search_fields = ('invoice_number', 'user__username', 'user__email')
    inlines = [InvoiceItemInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'payment_reference',
        'invoice',
        'payment_account',
        'amount',
        'payment_date',
        'payment_method',
    )
    list_filter = ('payment_method', 'payment_date')
    search_fields = ('payment_reference', 'invoice__invoice_number')

    #the changing of the title and header 
   
  
    admin.site.site_header = "ERP Finance System"
admin.site.site_title = "ERP System for Managing the Company"
admin.site.index_title = "The Management System"
