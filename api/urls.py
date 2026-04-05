from django.urls import path
from core.views import (
    GetOrCreateTransferAPIView,
    ApproveTransferAPIView,
    GetStockSummaryAPIView,
)


urlpatterns = [
    path(
        "branches/<uuid:id>/stock-summary/",
        GetStockSummaryAPIView.as_view(),
        name="stock-summary",
    ),
    path(
        "transfers/",
        GetOrCreateTransferAPIView.as_view(),
        name="stock-summary",
    ),
    path(
        "transfers/<uuid:id>/approve/",
        ApproveTransferAPIView.as_view(),
        name="stock-summary",
    ),
]
