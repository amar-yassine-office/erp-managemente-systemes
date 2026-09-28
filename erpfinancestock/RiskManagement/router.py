from ninja import Router
from ninja_jwt.authentication import JWTAuth

# تعريف الـ Router مع تفعيل حماية الـ JWT إجبارياً على مستوى موديول إدارة المخاطر بالكامل
router = Router(tags=["Risk Management"], auth=JWTAuth())