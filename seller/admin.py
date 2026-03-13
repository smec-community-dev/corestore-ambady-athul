from django.contrib import admin
from .models import (
    SellerProfile,
    Product,
    ProductVariant,
    ProductImage,
    Attribute,
    AttributeOption,
    VariantAttributeBridge,
    InventoryLog,
)

admin.site.register(SellerProfile)
admin.site.register(Product)
admin.site.register(ProductVariant)
admin.site.register(ProductImage)
admin.site.register(Attribute)
admin.site.register(AttributeOption)
admin.site.register(VariantAttributeBridge)
admin.site.register(InventoryLog)
