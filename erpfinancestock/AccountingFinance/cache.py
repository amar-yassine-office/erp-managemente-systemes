from django.core.cache import cache
from .models import Account, TaxRate, FiscalYear

# أوقات التخزين بالثواني
TTL_24_HOURS = 86400
TTL_12_HOURS = 43200


class AccountingCache:

    @staticmethod
    def get_active_accounts():
        """كاش لقائمة الحسابات النشطة (Chart of Accounts) لمدة 24 ساعة"""
        key = "accounting:accounts:active"
        data = cache.get(key)

        if data is None:
            data = list(
                Account.objects.filter(is_active=True).values(
                    "id", "code", "name", "account_type", "parent_id"
                )
            )
            cache.set(key, data, TTL_24_HOURS)

        return data

    @staticmethod
    def get_active_tax_rates():
        """كاش لأسعار الضرائب النشطة لمدة 24 ساعة"""
        key = "accounting:tax_rates:active"
        data = cache.get(key)

        if data is None:
            data = list(
                TaxRate.objects.filter(is_active=True).values(
                    "id", "name", "rate", "account_id"
                )
            )
            cache.set(key, data, TTL_24_HOURS)

        return data

    @staticmethod
    def get_open_fiscal_years():
        """كاش للسنوات المالية المفتوحة لمدة 12 ساعة"""
        key = "accounting:fiscal_years:open"
        data = cache.get(key)

        if data is None:
            data = list(
                FiscalYear.objects.filter(is_closed=False).values(
                    "id", "name", "start_date", "end_date"
                )
            )
            cache.set(key, data, TTL_12_HOURS)

        return data