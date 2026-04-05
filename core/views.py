from rest_framework.views import APIView
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from .models import Branch, Product
from rest_framework.response import Response
from .serializers import (
    CreateStockTransferSerializer,
    ApproveStockTransferSerializer,
    StockTransferSerializer,
)
from .services import StockTransferService
from .utils import APIErrorResponse
from .constants import StockTransferStatus
# Create your views here.


class GetOrCreateTransferAPIView(APIView):
    def post(self, request):
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
            )

        except NotFound as e:
            return APIErrorResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                message=e.detail,
            )
        except Exception:
            return APIErrorResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="An unexpected error occurred while processing the request.",
            )

    def get(self, request):
        stock_transfers = StockTransferService.filtered_transfered_entries(request)
        serializer = StockTransferSerializer(stock_transfers, many=True)
        return Response(
            {
                "message": "Stock transfer entries retrieved successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
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
