from django.db import models
import secrets
import string
from django.contrib.auth.models import AbstractUser
from .constants import (
    stock_transfer_status,
    StockTransferStatus,
    transfer_type_choice,
    TransferType,
)
import uuid
# Create your models here.


def generate_branch_code():
    prefix = "BR"
    string_pool = string.ascii_uppercase + string.digits
    random_code = "".join(secrets.choice(string_pool) for _ in range(6))
    return prefix + random_code


def generate_sku():
    prefix = "SKU"
    string_pool = string.ascii_uppercase + string.digits
    random_code = "".join(secrets.choice(string_pool) for _ in range(16 - len(prefix)))
    return prefix + random_code


class TimestampedModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(AbstractUser):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    role = models.CharField(max_length=20, default="user")


class Branch(TimestampedModel):
    name = models.CharField(max_length=120)
    code = models.CharField(
        max_length=20, unique=True, default=generate_branch_code, db_index=True
    )
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name="branches")

    def save(self, *args, **kwargs):
        if self.code is None:
            self.code = generate_branch_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.code})"


class Product(TimestampedModel):
    sku = models.CharField(
        max_length=16, unique=True, default=generate_sku, db_index=True
    )
    name = models.CharField(max_length=120)

    def save(self, *args, **kwargs):
        if self.sku is None:
            self.sku = generate_sku()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.sku})"


class Stock(TimestampedModel):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="stocks")
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="stocks"
    )
    quantity = models.PositiveIntegerField()

    class Meta:
        unique_together = ("branch", "product")

    def __str__(self):
        return f"{self.branch.name} - {self.product.name}: {self.quantity}"


class StockTransfer(TimestampedModel):
    from_branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="outgoing_transfers"
    )
    to_branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="incoming_transfers"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="transfers"
    )
    quantity = models.PositiveIntegerField()
    requested_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="requested_transfers"
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="approved_transfers",
        null=True,
        blank=True,
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    transfer_status = models.CharField(
        max_length=20,
        choices=stock_transfer_status,
        default=StockTransferStatus.PENDING,
    )
    transfer_type = models.CharField(
        max_length=20,
        choices=transfer_type_choice,
        default=TransferType.REQUEST,
    )

    def __str__(self):
        return f"{self.product.name} from {self.from_branch.name} to {self.to_branch.name} ({self.quantity})"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["from_branch", "to_branch", "product"],
                condition=models.Q(transfer_status=StockTransferStatus.PENDING),
                name="unique_transfer_pending",
            )
        ]
