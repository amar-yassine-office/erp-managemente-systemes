from django.core.cache import cache
from .models import MarketAsset, ResearchReport, AnalystRecommendation, FinancialMetric, MarketSentiment


class ResearchAnalyticsCacheService:
    """
    خدمة التخزين المؤقت المخصصة لتطبيق ResearchAnalytics.
    تتعامل مع التخزين والسحب والإبطال لأدوات التحليل والتقارير وتوصيات المحللين.
    """

    # =========================================================================
    # 1. MarketAsset Caching (الأصول المالية والرموز)
    # =========================================================================
    @staticmethod
    def get_active_assets():
        """
        تخزين قائمة الأصول المتاحة للتداول (الرمز، الاسم، الفئة، القطاع) لمدة 24 ساعة.
        هذه البيانات تعتبر Master Data تتغير بنسبة ضئيلة وتطلب في كل مكان.
        """
        cache_key = "research:assets:active_list"
        assets = cache.get(cache_key)

        if assets is None:
            assets = list(
                MarketAsset.objects.filter(is_active=True)
                .values('id', 'symbol', 'name', 'asset_class', 'sector', 'exchange')
            )
            cache.set(cache_key, assets, timeout=86400)  # 24 ساعة

        return assets

    @staticmethod
    def get_asset_detail_by_symbol(symbol: str):
        """تخزين تفاصيل أصل معين عن طريق الرمز (Symbol) لمدة 12 ساعة."""
        cache_key = f"research:asset:symbol:{symbol.upper()}"
        asset_data = cache.get(cache_key)

        if asset_data is None:
            try:
                asset = MarketAsset.objects.get(symbol__iexact=symbol)
                asset_data = {
                    'id': asset.id,
                    'symbol': asset.symbol,
                    'name': asset.name,
                    'asset_class': asset.asset_class,
                    'sector': asset.sector,
                    'exchange': asset.exchange,
                    'is_active': asset.is_active,
                }
                cache.set(cache_key, asset_data, timeout=43200)  # 12 ساعة
            except MarketAsset.DoesNotExist:
                return None

        return asset_data

    @staticmethod
    def invalidate_asset_cache(symbol: str = None):
        """مسح كاش قائمة الأصول والأصل المخصص عند التعديل."""
        cache.delete("research:assets:active_list")
        if symbol:
            cache.delete(f"research:asset:symbol:{symbol.upper()}")

    # =========================================================================
    # 2. ResearchReport Caching (تقارير الأبحاث والتحليلات)
    # =========================================================================
    @staticmethod
    def get_published_reports(limit: int = 20):
        """
        تخزين قائمة آخر التقارير المنشورة (العناوين والملخصات) لمدة ساعة.
        """
        cache_key = f"research:reports:published:limit_{limit}"
        reports = cache.get(cache_key)

        if reports is None:
            reports = list(
                ResearchReport.objects.filter(status='PUBLISHED')
                .select_related('author', 'asset')
                .values(
                    'id', 'title', 'summary', 'status', 'is_premium',
                    'published_at', 'author__username', 'asset__symbol'
                )[:limit]
            )
            for r in reports:
                if r['published_at']:
                    r['published_at'] = r['published_at'].isoformat()

            cache.set(cache_key, reports, timeout=3600)  # ساعة واحدة

        return reports

    @staticmethod
    def get_report_detail(report_id: int):
        """
        تخزين تفاصيل التقرير الكامل بأسلوب Caching لطويل الأجل (6 ساعات).
        حيث أن التقارير المنشورة نادرًا ما تنقح وتعدل بعد النشر.
        """
        cache_key = f"research:report:detail:{report_id}"
        report_data = cache.get(cache_key)

        if report_data is None:
            try:
                r = ResearchReport.objects.select_related('author', 'asset').get(id=report_id)
                if r.status != 'PUBLISHED':
                    return None  # لا نخزن التقارير غير المنشورة

                report_data = {
                    'id': r.id,
                    'title': r.title,
                    'summary': r.summary,
                    'content': r.content,
                    'is_premium': r.is_premium,
                    'published_at': r.published_at.isoformat() if r.published_at else None,
                    'author_id': r.author_id,
                    'author_name': r.author.username if r.author else None,
                    'asset_symbol': r.asset.symbol if r.asset else None,
                }
                cache.set(cache_key, report_data, timeout=21600)  # 6 ساعات
            except ResearchReport.DoesNotExist:
                return None

        return report_data

    @staticmethod
    def invalidate_report_cache(report_id: int = None):
        """مسح كاش التقارير المنشورة للتحديث الفوري."""
        # مسح كاش القوائم الشائعة
        cache.delete("research:reports:published:limit_20")
        cache.delete("research:reports:published:limit_50")
        if report_id:
            cache.delete(f"research:report:detail:{report_id}")

    # =========================================================================
    # 3. AnalystRecommendation Caching (توصيات المحللين والتسيعر المستهدف)
    # =========================================================================
    @staticmethod
    def get_asset_recommendations(asset_id: int):
        """
        تخزين جميع التوصيات النشطة لسهم أو أصل معين لمدة 30 دقيقة.
        """
        cache_key = f"research:asset:{asset_id}:recommendations"
        recs = cache.get(cache_key)

        if recs is None:
            recs = list(
                AnalystRecommendation.objects.filter(asset_id=asset_id, is_active=True)
                .select_related('analyst')
                .values(
                    'id', 'rating', 'current_price_at_rating', 'target_price',
                    'time_horizon_months', 'created_at', 'analyst__username'
                )
            )
            for item in recs:
                item['current_price_at_rating'] = float(item['current_price_at_rating'])
                item['target_price'] = float(item['target_price'])
                item['created_at'] = item['created_at'].isoformat()

            cache.set(cache_key, recs, timeout=1800)  # 30 دقيقة

        return recs

    @staticmethod
    def invalidate_recommendation_cache(asset_id: int):
        """إبطال كاش التوصيات فور صدور توصية جديدة."""
        cache.delete(f"research:asset:{asset_id}:recommendations")

    # =========================================================================
    # 4. FinancialMetric Caching (المؤشرات المالية الأساسية P/E, EPS)
    # =========================================================================
    @staticmethod
    def get_asset_financial_metrics(asset_id: int):
        """
        تخزين المؤشرات المالية التاريخية والربع سنوية للسهم لمدة 12 ساعة.
        (لأن القوائم المالية تصدر كل ربع سنة تقريباً).
        """
        cache_key = f"research:asset:{asset_id}:financial_metrics"
        metrics = cache.get(cache_key)

        if metrics is None:
            metrics = list(
                FinancialMetric.objects.filter(asset_id=asset_id)
                .values('period_date', 'pe_ratio', 'pb_ratio', 'eps', 'debt_to_equity', 'roe_pct', 'free_cash_flow')
            )
            for m in metrics:
                m['period_date'] = m['period_date'].isoformat()
                m['pe_ratio'] = float(m['pe_ratio']) if m['pe_ratio'] is not None else None
                m['pb_ratio'] = float(m['pb_ratio']) if m['pb_ratio'] is not None else None
                m['eps'] = float(m['eps']) if m['eps'] is not None else None
                m['debt_to_equity'] = float(m['debt_to_equity']) if m['debt_to_equity'] is not None else None
                m['roe_pct'] = float(m['roe_pct']) if m['roe_pct'] is not None else None
                m['free_cash_flow'] = float(m['free_cash_flow']) if m['free_cash_flow'] is not None else None

            cache.set(cache_key, metrics, timeout=43200)  # 12 ساعة

        return metrics

    @staticmethod
    def invalidate_metrics_cache(asset_id: int):
        """إبطال كاش المؤشرات عند إدخال نتائج مالية جديدة."""
        cache.delete(f"research:asset:{asset_id}:financial_metrics")

    # =========================================================================
    # 5. MarketSentiment Caching (انطباعات الأخبار والـ Sentiment)
    # =========================================================================
    @staticmethod
    def get_latest_asset_sentiment(asset_id: int):
        """
        تخزين آخر مؤشر انطباع سائد (Sentiment) للرمز لمدة 15 دقيقة فقط.
        (لأنه يتأثر بالأخبار العاجلة ووسائل التواصل بشكل سريع).
        """
        cache_key = f"research:asset:{asset_id}:latest_sentiment"
        sentiment_data = cache.get(cache_key)

        if sentiment_data is None:
            latest = MarketSentiment.objects.filter(asset_id=asset_id).first()
            if latest:
                sentiment_data = {
                    'id': latest.id,
                    'sentiment_score': float(latest.sentiment_score),
                    'label': latest.label,
                    'news_source_count': latest.news_source_count,
                    'summary': latest.summary,
                    'evaluated_at': latest.evaluated_at.isoformat(),
                }
                cache.set(cache_key, sentiment_data, timeout=900)  # 15 دقيقة
            else:
                return None

        return sentiment_data

    @staticmethod
    def invalidate_sentiment_cache(asset_id: int):
        """إبطال كاش الـ Sentiment عند احتساب قراءة جديدة."""
        cache.delete(f"research:asset:{asset_id}:latest_sentiment")