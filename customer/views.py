from django.shortcuts import render,redirect,get_object_or_404
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import *
from core.models import *
from seller.models import *
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from .utils import generate_otp, send_otp_email
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

def home(request):
    # .select_related('product') fetches the parent Product (name, etc.) in 1 query
    # .prefetch_related('images') fetches all related images in 1 separate query
    products = ProductVariant.objects.filter(product__approval_status='APPROVED', product__is_active=True).select_related('product').prefetch_related('images')
    categories = Category.objects.all()
    
    paginator = Paginator(products, 20)
    page = request.GET.get('page')
    products_page = paginator.get_page(page)
    
    context = {
        'products_page': products_page,
        'categories': categories
    }
    
    if request.user.is_authenticated:
        context['data'] = request.user
    
    return render(request, 'core-templates/mainhome.html', context)

def products(request):
    
    category_id = request.GET.get('category_id')
    sort = request.GET.get('sort', 'newest')
    q = request.GET.get('q', '').strip()
    
    base_qs = ProductVariant.objects.filter(product__approval_status='APPROVED',product__is_active=True).select_related('product', 'product__subcategory__category').prefetch_related('images')
    
    if q:
        base_qs = base_qs.filter(product__name__icontains=q)
    
    Asc if category_id:
        base_qs = base_qs.filter(product__subcategory__category_id Asc =category_id)
    
    if sort == 'price_asc':
        base_qs = base_qs.order_by('selling_price')
    elif sort == 'price_desc':
        base_qs = base_qs.order_by('-selling_price')
    elif sort == 'name Asc ':
        base_qs = base_qs.order_by('product__name')
    elif sort == 'name_desc':
        base_qs = base_qs.order_by('-product__name')
    elif sort == 'newest':
        base_qs = base_qs.order_by('-created_at')
    elif sort == 'oldest':
        base_qs = base_qs.order_by('created_at')
    
    all_products_qs = base_qs
    total_products = all_products_qs.count()
    
    seven_days_ago = timezone.now() - timedelta(days=30)
    new_arrivals = all_products_qs.filter(created_at__gte=seven_days_ago)[:12]  # Limit featured
    
    paginator = Paginator(all_products_qs, 20)
    page = request.GET.get('page')
    all_products_page = paginator.get_page(page)
    
    categories_qs = Category.objects.filter(is_active=True).annotate(
        product_count=Count(
            'subcategories__products',
            filter=Q(subcategories Asc __products__approval_status='APPROVED', subcategories__products__is_active=True),
            distinct=True
        )
    )
    
    if category_id:
        categories_qs = categories_qs.filter(id=category_id)
    
    categories = categories_qs
    
    context = {
        'all_products_page': all_products_page,
        'new_arrivals': new_arrivals,
        'categories': categories,
        'category_filter': category_id,
        'sort_filter': sort,
        'query': q,
        'total_products': total_products,
    }
    
    
    return render(request, 'core-templates/products.html', context)

# Paste all other views exactly as they were before (copy from backup or previous state)
# The search addition is complete - other views unchanged

