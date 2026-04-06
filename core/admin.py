from django.contrib import admin
from .models import Branch, Product, StockTransfer, User, Stock

# Register your models here.


admin.site.register(Branch)
admin.site.register(Stock)
admin.site.register(Product)
admin.site.register(StockTransfer)
admin.site.register(User)
