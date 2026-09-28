from ninja import Router
from ninja_jwt.authentication import JWTAuth

# تهيئة الـ Router مع تفعيل المصادقة بـ JWT إجبارياً على مستوى الموديول بالكامل
router = Router(tags=["Portfolio Management"], auth=JWTAuth())