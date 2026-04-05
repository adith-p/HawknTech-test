from .models import Branch, Product, Stock, StockTransfer
from .constants import StockTransferStatus, TransferType
from rest_framework.exceptions import NotFound, ValidationError
from django.db import transaction, IntegrityError
from django.utils import timezone


class BranchService:
    @staticmethod
    def get_branch_by_id(branch_id):
        try:
            return Branch.objects.get(id=branch_id)
        except Branch.DoesNotExist:
            raise NotFound(detail="Branch with this id does not exist.")


class ProductService:
    @staticmethod
    def get_product_by_sku(sku):
        try:
            return Product.objects.get(sku=sku)
        except Product.DoesNotExist:
            raise NotFound(detail="Product with this SKU does not exist.")


class StockTransferService:
    @staticmethod
    def get_transfer_by_id(transfer_id):
        try:
            return StockTransfer.objects.select_for_update().get(id=transfer_id)
        except StockTransfer.DoesNotExist:
            raise NotFound(detail="Stock transfer with this id does not exist.")

    @staticmethod
    def create_transfer_entry(validated_data, branch_admin):

        transfer_type = validated_data.get("transfer_type")
        to_branch = BranchService.get_branch_by_id(validated_data.get("to_branch"))
        from_branch = BranchService.get_branch_by_id(validated_data.get("from_branch"))

        if transfer_type == TransferType.REQUEST:
            if to_branch.admin != branch_admin:
                raise ValidationError(
                    detail=f"Only the admin of the {to_branch.code} can create a transfer request."
                )
        if transfer_type == TransferType.OFFER:
            if from_branch.admin != branch_admin:
                raise ValidationError(
                    detail=f"Only the admin of the {from_branch.code} can create a transfer offer."
                )

        product = ProductService.get_product_by_sku(validated_data.get("product_sku"))
        with transaction.atomic():
            try:
                transfer_entry = StockTransfer.objects.create(
                    from_branch=from_branch,
                    to_branch=to_branch,
                    product=product,
                    quantity=validated_data.get("quantity"),
                    requested_by=branch_admin,
                    transfer_type=transfer_type,
                )
            except IntegrityError:
                raise ValidationError(
                    detail="Stock transfer entry already exists with transfer status pending."
                )
            return transfer_entry

    @staticmethod
    @transaction.atomic
    def approve_transfer_entry(transfer_id, validated_data, branch_admin):

        transfer_entry = StockTransferService.get_transfer_by_id(transfer_id)
        transfer_type = transfer_entry.transfer_type

        if transfer_entry.transfer_status != StockTransferStatus.PENDING:
            raise ValidationError(
                detail="This transfer has already been processed and cannot be modified."
            )

        if transfer_type == TransferType.REQUEST:
            if transfer_entry.from_branch.admin != branch_admin:
                raise ValidationError(
                    detail=f"Only the admin of the {transfer_entry.from_branch.code} can approve a transfer request."
                )
        if transfer_type == TransferType.OFFER:
            if transfer_entry.to_branch.admin != branch_admin:
                raise ValidationError(
                    detail=f"Only the admin of the {transfer_entry.to_branch.code} can approve a transfer offer."
                )

        if validated_data.get("transfer_status") == StockTransferStatus.REJECTED:
            transfer_entry.transfer_status = StockTransferStatus.REJECTED
            transfer_entry.save()
            return transfer_entry
        if validated_data.get("transfer_status") == StockTransferStatus.APPROVED:
            # check 1
            try:
                from_br_stock = Stock.objects.select_for_update().get(
                    branch=transfer_entry.from_branch,
                    product=transfer_entry.product,
                )
            except Stock.DoesNotExist:
                raise NotFound(
                    detail=f"Can't approve transfer. Stock entry for the product does not exist in the {transfer_entry.from_branch.name}"
                )

            if from_br_stock.quantity < transfer_entry.quantity:
                raise ValidationError(
                    detail=f"Can't approve transfer. Insufficient stock quantity in the {transfer_entry.from_branch.name}"
                )

            to_br_stock, _ = Stock.objects.select_for_update().get_or_create(
                branch=transfer_entry.to_branch,
                product=transfer_entry.product,
                defaults={"quantity": 0},
            )

            from_br_stock.quantity -= transfer_entry.quantity
            to_br_stock.quantity += transfer_entry.quantity

            from_br_stock.save()
            to_br_stock.save()

            transfer_entry.transfer_status = StockTransferStatus.APPROVED
            transfer_entry.approved_by = branch_admin
            transfer_entry.approved_at = timezone.now()
            transfer_entry.save()
            return transfer_entry


class StockSummaryService:
    @staticmethod
    def get_stock_summary(branch_id):
        target_branch = BranchService.get_branch_by_id(branch_id)
        stock_entries = Stock.objects.filter(branch=target_branch).select_related(
            "product"
        )

        return stock_entries
