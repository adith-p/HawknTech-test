from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views import (
    GetOrCreateTransferViewset,
    ApproveTransferAPIView,
    GetStockSummaryAPIView,
    ListBranchAPIView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

router = DefaultRouter()
router.register(r"transfers", GetOrCreateTransferViewset, basename="stock-transfer")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "token/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),
    path("branches/", ListBranchAPIView.as_view(), name="branch-list"),
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
    path(
        "schema/",
        SpectacularAPIView.as_view(),
        name="schema",
    ),
    path(
        "docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]
