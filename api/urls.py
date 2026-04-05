from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views import (
    GetOrCreateTransferViewset,
    ApproveTransferAPIView,
    GetStockSummaryAPIView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

router = DefaultRouter()
router.register(r"transfers", GetOrCreateTransferViewset, basename="stock-transfer")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "api/token/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "api/token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),
    path(
        "branches/<uuid:id>/stock-summary/",
        GetStockSummaryAPIView.as_view(),
        name="stock-summary",
    ),
    path(
        "transfers/<uuid:id>/approve/",
        ApproveTransferAPIView.as_view(),
        name="stock-transfer-approve",
    ),
]
