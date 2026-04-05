from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from .models import Branch, Product, StockTransfer
from rest_framework.response import Response
from .serializers import (
    CreateStockTransferSerializer,
    ApproveStockTransferSerializer,
    StockTransferSerializer,
)
from .services import StockTransferService
from .utils import APIErrorResponse
from .constants import StockTransferStatus
from rest_framework.pagination import CursorPagination
# Create your views here.


class StockTransferPagination(CursorPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100
    ordering = "-created_at"


class GetOrCreateTransferViewset(ModelViewSet):
    queryset = StockTransfer.objects.select_related(
        "from_branch", "to_branch", "product", "requested_by", "approved_by"
    ).all()
    serializer_class = StockTransferSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = [
        "from_branch__code",
        "to_branch__code",
        "product__sku",
        "transfer_status",
    ]
    pagination_class = StockTransferPagination

    def create(self, request):
        try:
            serializer = CreateStockTransferSerializer(data=request.data)
            if serializer.is_valid():
                StockTransferService.create_transfer_entry(
                    serializer.validated_data, request.user
                )
                return Response(
                    {"message": "Stock transfer request created successfully."},
                    status=status.HTTP_201_CREATED,
                )
            return APIErrorResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                serial_valid=serializer.errors,
                data=serializer.errors,
            )

        except NotFound as e:
            return APIErrorResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                message=e.detail,
            )
        except Exception as e:
            return APIErrorResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                # message="An unexpected error occurred while processing the request.",
                message=str(e),
            )


class ApproveTransferAPIView(APIView):
    def post(self, request, id):
        try:
            serializer = ApproveStockTransferSerializer(data=request.data)
            if serializer.is_valid():
                transfer_entry = StockTransferService.approve_transfer_entry(
                    id, serializer.validated_data, request.user
                )
                if transfer_entry.transfer_status == StockTransferStatus.REJECTED:
                    return Response(
                        {
                            "message": "Stock transfer request rejected.",
                            "data": StockTransferSerializer(transfer_entry).data,
                        },
                        status=status.HTTP_200_OK,
                    )
                return Response(
                    {
                        "message": "Stock transfer request approved successfully.",
                        "data": StockTransferSerializer(transfer_entry).data,
                    },
                    status=status.HTTP_200_OK,
                )
            return APIErrorResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                serial_valid=serializer.errors,
            )

        except NotFound as e:
            return APIErrorResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                message=e.detail,
            )

        except ValidationError as e:
            return APIErrorResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=e.detail,
            )
        except Exception as e:
            return APIErrorResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="An unexpected error occurred while processing the request.",
                # message=str(e),
            )


class GetStockSummaryAPIView(APIView):
    def get(self, request):
        pass
