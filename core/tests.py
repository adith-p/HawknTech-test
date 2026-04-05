from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import User, Branch, Product, Stock, StockTransfer
from .constants import StockTransferStatus, TransferType


class BaseTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # 2 branch admins
        self.admin_1 = User.objects.create_user(
            username="admin1", password="admin1", role="branch_admin"
        )
        self.admin_2 = User.objects.create_user(
            username="admin2", password="admin2", role="branch_admin"
        )
        self.normal_user = User.objects.create_user(
            username="normal_user", password="normal_user", role="user"
        )

        # admin_1 owns branch_1, admin_2 owns branch_2
        self.branch_1 = Branch.objects.create(name="branch1", admin=self.admin_1)
        self.branch_2 = Branch.objects.create(name="branch2", admin=self.admin_2)

        # 2 products
        self.product_1 = Product.objects.create(name="Maggie")
        self.product_2 = Product.objects.create(name="Milk")

        # branch_1 starts with stock for both products
        self.stock_1 = Stock.objects.create(
            branch=self.branch_1, product=self.product_1, quantity=100
        )
        self.stock_2 = Stock.objects.create(
            branch=self.branch_1, product=self.product_2, quantity=100
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)


def request_payload(branch_1, branch_2, product, quantity=30):
    return {
        "from_branch": str(branch_1.id),
        "to_branch": str(branch_2.id),
        "product_sku": product.sku,
        "quantity": quantity,
        "transfer_type": TransferType.REQUEST,
    }


class TransferSuccessTest(BaseTestCase):
    """Test 1: Full happy-path flow for a REQUEST transfer."""

    def test_happy_path_transfer_update(self):
        # Step 1: admin_2 creates the REQUEST
        self.authenticate(self.admin_2)
        response = self.client.post(
            reverse("stock-transfer-list"),
            request_payload(self.branch_1, self.branch_2, self.product_1, quantity=30),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        transfer = StockTransfer.objects.get(
            from_branch=self.branch_1,
            to_branch=self.branch_2,
            product=self.product_1,
        )
        self.assertEqual(transfer.transfer_status, StockTransferStatus.PENDING)

        # Step 2: admin_1 approves the REQUEST
        self.authenticate(self.admin_1)
        response = self.client.post(
            reverse("stock-transfer-approve", kwargs={"id": transfer.id}),
            {"transfer_status": StockTransferStatus.APPROVED},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Stock deducted from branch_1
        self.stock_1.refresh_from_db()
        self.assertEqual(self.stock_1.quantity, 70)

        # Stock added to branch_2
        branch_2_stock = Stock.objects.get(branch=self.branch_2, product=self.product_1)
        self.assertEqual(branch_2_stock.quantity, 30)

        # Transfer marked APPROVED with audit fields populated
        transfer.refresh_from_db()
        self.assertEqual(transfer.transfer_status, StockTransferStatus.APPROVED)
        self.assertIsNotNone(transfer.approved_by)
        self.assertIsNotNone(transfer.approved_at)
        self.assertEqual(transfer.approved_by, self.admin_1)


class InsufficientStockTest(BaseTestCase):
    """Test 2: Approval fails when from_branch stock is less than requested qty."""

    def test_approve_fails_when_insufficient_stock(self):
        # admin_2 requests 101 units — branch_1 only has 100
        self.authenticate(self.admin_2)
        response = self.client.post(
            reverse("stock-transfer-list"),
            request_payload(self.branch_1, self.branch_2, self.product_1, quantity=101),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        transfer = StockTransfer.objects.get(
            from_branch=self.branch_1,
            to_branch=self.branch_2,
            product=self.product_1,
        )

        # admin_1 tries to approve — should fail
        self.authenticate(self.admin_1)
        response = self.client.post(
            reverse("stock-transfer-approve", kwargs={"id": transfer.id}),
            {"transfer_status": StockTransferStatus.APPROVED},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Stock must remain untouched
        self.stock_1.refresh_from_db()
        self.assertEqual(self.stock_1.quantity, 100)

        # Transfer must still be PENDING
        transfer.refresh_from_db()
        self.assertEqual(transfer.transfer_status, StockTransferStatus.PENDING)


class PermissionTest(BaseTestCase):
    """Test 3: Role-based access — only branch_admin can write."""

    def test_regular_user_cannot_create_transfer(self):
        self.authenticate(self.normal_user)
        response = self.client.post(
            reverse("stock-transfer-list"),
            request_payload(self.branch_1, self.branch_2, self.product_1),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(StockTransfer.objects.count(), 0)

    def test_regular_user_cannot_approve_transfer(self):
        # Create a valid transfer first as admin_2
        self.authenticate(self.admin_2)
        self.client.post(
            reverse("stock-transfer-list"),
            request_payload(self.branch_1, self.branch_2, self.product_1),
            format="json",
        )
        transfer = StockTransfer.objects.first()

        # normal_user attempts to approve
        self.authenticate(self.normal_user)
        response = self.client.post(
            reverse("stock-transfer-approve", kwargs={"id": transfer.id}),
            {"transfer_status": StockTransferStatus.APPROVED},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        transfer.refresh_from_db()
        self.assertEqual(transfer.transfer_status, StockTransferStatus.PENDING)


class DuplicateTransferTest(BaseTestCase):
    """Test 4: Duplicate pending transfer for same from/to/product is rejected."""

    def test_duplicate_pending_transfer_rejected(self):
        self.authenticate(self.admin_2)
        payload = request_payload(self.branch_1, self.branch_2, self.product_1)

        response1 = self.client.post(
            reverse("stock-transfer-list"), payload, format="json"
        )
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        response2 = self.client.post(
            reverse("stock-transfer-list"), payload, format="json"
        )
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)

        # Exactly one record must exist
        self.assertEqual(StockTransfer.objects.count(), 1)


class StockSummaryTest(BaseTestCase):
    """Test 5: Stock summary returns correct data for the requested branch."""

    def test_stock_summary_returns_correct_data(self):
        self.authenticate(self.admin_1)
        response = self.client.get(
            reverse("stock-summary", kwargs={"id": self.branch_1.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()["data"]
        self.assertEqual(len(data), 2)

        by_sku = {item["product_sku"]: item for item in data}
        self.assertIn(self.product_1.sku, by_sku)
        self.assertIn(self.product_2.sku, by_sku)
        self.assertEqual(by_sku[self.product_1.sku]["quantity"], 100)
        self.assertEqual(by_sku[self.product_2.sku]["quantity"], 100)


class WrongBranchAdminCreateTest(BaseTestCase):
    """Test 6: Admin of from_branch cannot create a REQUEST (only to_branch admin can)."""

    def test_from_branch_admin_cannot_create_request_transfer(self):
        # admin_1 owns branch_1 (from_branch), not branch_2 (to_branch)
        self.authenticate(self.admin_1)
        response = self.client.post(
            reverse("stock-transfer-list"),
            request_payload(self.branch_1, self.branch_2, self.product_1),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(StockTransfer.objects.count(), 0)


class WrongBranchAdminApproveTest(BaseTestCase):
    """Test 7: Admin of to_branch cannot approve a REQUEST (only from_branch admin can)."""

    def test_to_branch_admin_cannot_approve_request_transfer(self):
        # admin_2 creates the REQUEST correctly (owns to_branch)
        self.authenticate(self.admin_2)
        self.client.post(
            reverse("stock-transfer-list"),
            request_payload(self.branch_1, self.branch_2, self.product_1, quantity=10),
            format="json",
        )

        transfer = StockTransfer.objects.get(
            from_branch=self.branch_1,
            to_branch=self.branch_2,
            product=self.product_1,
        )

        # admin_2 tries to approve — only admin_1 (from_branch) can do this
        response = self.client.post(
            reverse("stock-transfer-approve", kwargs={"id": transfer.id}),
            {"transfer_status": StockTransferStatus.APPROVED},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Stock untouched
        self.stock_1.refresh_from_db()
        self.assertEqual(self.stock_1.quantity, 100)

        # Transfer still PENDING
        transfer.refresh_from_db()
        self.assertEqual(transfer.transfer_status, StockTransferStatus.PENDING)


class OfferTransferSuccessTest(BaseTestCase):
    """Test 8: OFFER-type transfer — from_branch admin creates, to_branch admin approves."""

    def test_offer_transfer_happy_path(self):
        # admin_1 (owns branch_1 = from_branch) creates the OFFER
        self.authenticate(self.admin_1)
        response = self.client.post(
            reverse("stock-transfer-list"),
            {
                "from_branch": str(self.branch_1.id),
                "to_branch": str(self.branch_2.id),
                "product_sku": self.product_1.sku,
                "quantity": 20,
                "transfer_type": TransferType.OFFER,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        transfer = StockTransfer.objects.get(
            from_branch=self.branch_1,
            to_branch=self.branch_2,
            product=self.product_1,
        )
        self.assertEqual(transfer.transfer_type, TransferType.OFFER)
        self.assertEqual(transfer.transfer_status, StockTransferStatus.PENDING)

        # admin_2 (owns branch_2 = to_branch) approves the OFFER
        self.authenticate(self.admin_2)
        response = self.client.post(
            reverse("stock-transfer-approve", kwargs={"id": transfer.id}),
            {"transfer_status": StockTransferStatus.APPROVED},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify stock moved correctly
        self.stock_1.refresh_from_db()
        self.assertEqual(self.stock_1.quantity, 80)

        branch_2_stock = Stock.objects.get(branch=self.branch_2, product=self.product_1)
        self.assertEqual(branch_2_stock.quantity, 20)

        transfer.refresh_from_db()
        self.assertEqual(transfer.transfer_status, StockTransferStatus.APPROVED)
        self.assertEqual(transfer.approved_by, self.admin_2)


class TransferTypeValidationTest(BaseTestCase):
    """Test 9: transfer_type field must be REQUEST or OFFER — anything else is rejected."""

    def test_invalid_transfer_type_string_rejected(self):
        """A transfer_type value outside [REQUEST, OFFER] must return 400."""
        self.authenticate(self.admin_2)
        response = self.client.post(
            reverse("stock-transfer-list"),
            {
                "from_branch": str(self.branch_1.id),
                "to_branch": str(self.branch_2.id),
                "product_sku": self.product_1.sku,
                "quantity": 10,
                "transfer_type": "SOME_TYPE",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(StockTransfer.objects.count(), 0)

    def test_missing_transfer_type_rejected(self):
        """Omitting transfer_type entirely must return 400."""
        self.authenticate(self.admin_2)
        response = self.client.post(
            reverse("stock-transfer-list"),
            {
                "from_branch": str(self.branch_1.id),
                "to_branch": str(self.branch_2.id),
                "product_sku": self.product_1.sku,
                "quantity": 10,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(StockTransfer.objects.count(), 0)

    def test_offer_wrong_admin_cannot_create(self):
        """
        OFFER rule: only from_branch admin can create.
        admin_2 (owns branch_2 = to_branch) tries to create an OFFER where
        from_branch=branch_1 — must be rejected.
        """
        self.authenticate(self.admin_2)
        response = self.client.post(
            reverse("stock-transfer-list"),
            {
                "from_branch": str(self.branch_1.id),
                "to_branch": str(self.branch_2.id),
                "product_sku": self.product_1.sku,
                "quantity": 10,
                "transfer_type": TransferType.OFFER,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(StockTransfer.objects.count(), 0)
