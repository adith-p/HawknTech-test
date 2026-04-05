from rest_framework import serializers
from rest_framework.serializers import ModelSerializer, Serializer
from .models import Product, Branch, StockTransfer
from .constants import StockTransferStatus
from django.contrib.auth import get_user_model

User = get_user_model()


class ProductSerializer(ModelSerializer):
    class Meta:
        model = Product
        fields = ("sku", "name")


class BranchSerializer(ModelSerializer):
    class Meta:
        model = Branch
        fields = ("code", "name", "admin")


class GetStockSummarySerializer(Serializer):
    Branch = BranchSerializer()
    catalog = ProductSerializer(many=True)


class CreateStockTransferSerializer(Serializer):
    from_branch = serializers.UUIDField()
    to_branch = serializers.UUIDField()
    product_sku = serializers.CharField()
    quantity = serializers.IntegerField()

    def validate_product_sku(self, data):
        if not Product.objects.filter(sku=data).exists():
            raise serializers.ValidationError("Product with this SKU does not exist.")
        return data


class ApproveStockTransferSerializer(Serializer):
    transfer_status = serializers.ChoiceField(
        choices=[StockTransferStatus.APPROVED, StockTransferStatus.REJECTED]
    )


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email")


class StockTransferSerializer(ModelSerializer):
    from_branch = BranchSerializer()
    to_branch = BranchSerializer()
    product = ProductSerializer()
    requested_by = UserSerializer()
    approved_by = UserSerializer()

    class Meta:
        model = StockTransfer
        fields = (
            "id",
            "from_branch",
            "to_branch",
            "product",
            "quantity",
            "requested_by",
            "approved_by",
            "approved_at",
            "transfer_status",
        )
