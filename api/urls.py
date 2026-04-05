from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views import (
    GetOrCreateTransferViewset,
    ApproveTransferAPIView,
    GetStockSummaryAPIView,
)


router = DefaultRouter()
router.register(r"transfers", GetOrCreateTransferViewset, basename="stock-transfer")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "branches/<uuid:id>/stock-summary/",
        GetStockSummaryAPIView.as_view(),
        name="stock-summary",
    ),
    path(
        "transfers/<uuid:id>/approve/",
        ApproveTransferAPIView.as_view(),
        name="stock-summary",
    ),
]
