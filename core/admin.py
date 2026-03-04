from django.contrib import admin
from .models import Category,SubCategory,User

# Register your models here.
admin.site.register(Category)
admin.site.register(SubCategory)
admin.site.register(User)
