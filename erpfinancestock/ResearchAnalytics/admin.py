from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import (
    AnalystRecommendation,
    FinancialMetric,
    MarketAsset,
    MarketSentiment,
    ResearchReport,
)


class AnalystRecommendationInline(admin.TabularInline):
    model = AnalystRecommendation
    extra = 0
    fields = ('analyst', 'rating', 'current_price_at_rating', 'target_price', 'is_active')


class FinancialMetricInline(admin.TabularInline):
    model = FinancialMetric
    extra = 0
    max_num = 4  # Display last 4 quarters


@admin.register(MarketAsset)
class MarketAssetAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'name', 'asset_class', 'sector', 'exchange', 'is_active')
    list_filter = ('asset_class', 'sector', 'is_active')
    search_fields = ('symbol', 'name', 'sector')
    inlines = [FinancialMetricInline]


@admin.register(ResearchReport)
class ResearchReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'asset', 'author', 'status', 'is_premium', 'published_at')
    list_filter = ('status', 'is_premium', 'created_at', 'published_at')
    search_fields = ('title', 'summary', 'asset__symbol', 'author__username')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [AnalystRecommendationInline]

    fieldsets = (
        ('Report Metadata', {'fields': ('title', 'asset', 'author', 'status', 'is_premium')}),
        ('Content Summary', {'fields': ('summary', 'content')}),
        ('Publication Dates', {'fields': ('published_at', 'created_at', 'updated_at')}),
    )


@admin.register(AnalystRecommendation)
class AnalystRecommendationAdmin(admin.ModelAdmin):
    list_display = (
        'asset',
        'analyst',
        'rating',
        'current_price_at_rating',
        'target_price',
        'time_horizon_months',
        'is_active',
        'created_at',
    )
    list_filter = ('rating', 'is_active', 'created_at')
    search_fields = ('asset__symbol', 'analyst__username')


@admin.register(FinancialMetric)
class FinancialMetricAdmin(admin.ModelAdmin):
    list_display = ('asset', 'period_date', 'pe_ratio', 'pb_ratio', 'eps', 'debt_to_equity')
    list_filter = ('period_date',)
    search_fields = ('asset__symbol',)


@admin.register(MarketSentiment)
class MarketSentimentAdmin(admin.ModelAdmin):
    list_display = ('asset', 'label', 'sentiment_score', 'news_source_count', 'evaluated_at')
    list_filter = ('label', 'evaluated_at')
    search_fields = ('asset__symbol',)
    