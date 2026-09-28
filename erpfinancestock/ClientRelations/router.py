from ninja import Router
from ninja_jwt.authentication import JWTAuth

router = Router(tags=["Client Relations & CRM"], auth=JWTAuth())