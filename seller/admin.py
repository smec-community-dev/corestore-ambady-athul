from django.contrib import admin
from .models import Product,ProductVariant,ProductImage,Attribute,AttributeOption,VariantAttributeBridge
# Register your models here.
admin.site.register(Product)
admin.site.register(ProductImage)
admin.site.register(ProductVariant)
admin.site.register(Attribute)