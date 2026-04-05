from .models import Branch, Product, Stock, StockTransfer
from .constants import StockTransferStatus
from rest_framework.exceptions import NotFound, ValidationError
from django.db import transaction
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

        to_branch = BranchService.get_branch_by_id(validated_data.get("to_branch"))
        if to_branch.admin != branch_admin:
            raise ValidationError(
                detail=f"Only the admin of the {to_branch.code} can create a transfer request."
            )

        from_branch = BranchService.get_branch_by_id(validated_data.get("from_branch"))
        product = ProductService.get_product_by_sku(validated_data.get("product_sku"))
        with transaction.atomic():
            transfer_entry = StockTransfer.objects.create(
                from_branch=from_branch,
                to_branch=to_branch,
                product=product,
                quantity=validated_data.get("quantity"),
                requested_by=branch_admin,
            )
            return transfer_entry

    @staticmethod
    def approve_transfer_entry(transfer_id, validated_data, branch_admin):
        transfer_entry = StockTransferService.get_transfer_by_id(transfer_id)

        with transaction.atomic():
            transfer_entry.approved_by = branch_admin
            transfer_entry.approved_at = timezone.now()
            if transfer_entry.from_branch.admin != branch_admin:
                raise ValidationError(
                    detail=f"Only the admin of the {transfer_entry.from_branch.code} can approve or reject the transfer."
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
                transfer_entry.approved_at = timezone.now()
                transfer_entry.save()
                return transfer_entry

    @staticmethod
    def filtered_transfered_entries(request):
        qp = request.query_params

        from_branch = qp.get("from_branch")
        to_branch = qp.get("to_branch")
        product = qp.get("product")

        transfer_entries = StockTransfer.objects.select_related(
            "from_branch", "to_branch", "product", "requested_by", "approved_by"
        ).all()

        if from_branch:
            transfer_entries = transfer_entries.filter(from_branch__code=from_branch)
        if to_branch:
            transfer_entries = transfer_entries.filter(to_branch__code=to_branch)
        if product:
            transfer_entries = transfer_entries.filter(product__sku=product)

        return transfer_entries
