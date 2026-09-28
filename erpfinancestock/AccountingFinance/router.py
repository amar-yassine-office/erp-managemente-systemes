from ninja import Router
from ninja_jwt.authentication import JWTAuth

# تعريف الراوتر الخاص بالمحاسبة والمالية مع تفعيل الحماية بإلزامية JWT
router = Router(tags=["Accounting & Finance"], auth=JWTAuth())
