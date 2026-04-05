from django.core.management.base import BaseCommand
from core.models import User, Branch, Product, Stock, StockTransfer


class Command(BaseCommand):
    help = "Seed the database with demo data"

    def handle(self, *args, **kwargs):
        self.stdout.write("Clearing existing data...")

        StockTransfer.objects.all().delete()
        Stock.objects.all().delete()
        Branch.objects.all().delete()
        Product.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

        # ── Users ──────────────────────────────────────
        admin_1 = User.objects.create_user(
            username="admin1", password="admin1", role="branch_admin"
        )
        admin_2 = User.objects.create_user(
            username="admin2", password="admin2", role="branch_admin"
        )
        User.objects.create_user(
            username="normal_user", password="normal_user", role="user"
        )

        # ── Branches ───────────────────────────────────
        branch_1 = Branch.objects.create(name="branch1", admin=admin_1)
        branch_2 = Branch.objects.create(name="branch2", admin=admin_2)

        # ── Products ───────────────────────────────────
        product_1 = Product.objects.create(name="Maggie")
        product_2 = Product.objects.create(name="Milk")

        # ── Stock ──────────────────────────────────────
        Stock.objects.create(branch=branch_1, product=product_1, quantity=100)
        Stock.objects.create(branch=branch_1, product=product_2, quantity=100)

        self.stdout.write(self.style.SUCCESS("Done!"))
        self.stdout.write("")
        self.stdout.write(
            f"  admin1 / admin1       →  {branch_1.name} ({branch_1.code})"
        )
        self.stdout.write(
            f"  admin2 / admin2       →  {branch_2.name} ({branch_2.code})"
        )
        self.stdout.write("normal_user / normal_user  →  no branch")
        self.stdout.write(f"  product_1  →  {product_1.name} ({product_1.sku})")
        self.stdout.write(f"  product_2  →  {product_2.name} ({product_2.sku})")
