from django.shortcuts import render,redirect,get_object_or_404
from django.urls import reverse
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import *
from core.models import *
from seller.models import *
from django.contrib.auth import login,logout,authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Avg
from .utils import generate_otp, send_otp_email
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from core.decorator import customer_required


User = get_user_model()

def home(request):
    # .select_related('product') fetches the parent Product (name, etc.) in 1 query
    # .prefetch_related('images') fetches all related images in 1 separate query
    products = ProductVariant.objects.filter(product__approval_status='APPROVED', product__is_active=True).select_related('product').prefetch_related('images').annotate(
        avg_rating=Avg('product__reviews__rating'),
        review_count=Count('product__reviews', distinct=True),
        star_5=Count('product__reviews', filter=Q(product__reviews__rating=5), distinct=True),
        star_4=Count('product__reviews', filter=Q(product__reviews__rating=4), distinct=True),
        star_3=Count('product__reviews', filter=Q(product__reviews__rating=3), distinct=True),
        star_2=Count('product__reviews', filter=Q(product__reviews__rating=2), distinct=True),
        star_1=Count('product__reviews', filter=Q(product__reviews__rating=1), distinct=True)
    )
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


@customer_required
def buy_now_checkout(request, slug):
    """
    Buy Now from single product - clear cart and add single item with POST quantity
    """
    variant = get_object_or_404(ProductVariant.objects.select_related('product'), slug=slug)
    
    if variant.stock_quantity <= 0:
        messages.error(request, 'Item out of stock.')
        return redirect('product_single', slug=slug)
    
    # Get quantity from POST, validate and default to 1
    quantity = 1
    if request.method == 'POST':
        try:
            qty = int(request.POST.get('quantity', 1))
            quantity = max(1, min(qty, variant.stock_quantity))
        except (ValueError, TypeError):
            quantity = 1
    
    # Get or create cart
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Clear existing items for Buy Now (replace cart)
    cart.items.all().delete()
    
    # Add single item with quantity
    CartItem.objects.create(
        cart=cart,
        variant=variant,
        quantity=quantity,
        price_at_time=variant.selling_price
    )
    
    # Set session flag for single checkout detection
    request.session['single_checkout'] = True
    request.session['checkout_back_product'] = slug
    
    messages.success(request, f'{quantity} x {variant.product.name} added for quick checkout!')
    return redirect('checkout')

def products(request):
    
    category_id = request.GET.get('category_id')
    sort = request.GET.get('sort', 'newest')
    
    base_qs = ProductVariant.objects.filter(
        product__approval_status='APPROVED',
        product__is_active=True,
        slug__isnull=False,
        slug__regex=r'^[-a-zA-Z0-9_]+$'
    ).select_related('product', 'product__subcategory__category').prefetch_related('images').annotate(
        avg_rating=Avg('product__reviews__rating'),
        review_count=Count('product__reviews', distinct=True),
        star_5=Count('product__reviews', filter=Q(product__reviews__rating=5), distinct=True),
        star_4=Count('product__reviews', filter=Q(product__reviews__rating=4), distinct=True),
        star_3=Count('product__reviews', filter=Q(product__reviews__rating=3), distinct=True),
        star_2=Count('product__reviews', filter=Q(product__reviews__rating=2), distinct=True),
        star_1=Count('product__reviews', filter=Q(product__reviews__rating=1), distinct=True)
    )

    
    if category_id:
        base_qs = base_qs.filter(product__subcategory__category_id=category_id)
    
    if sort == 'price_asc':
        base_qs = base_qs.order_by('selling_price')
    elif sort == 'price_desc':
        base_qs = base_qs.order_by('-selling_price')
    elif sort == 'name_asc':
        base_qs = base_qs.order_by('product__name')
    elif sort == 'name_desc':
        base_qs = base_qs.order_by('-product__name')
    elif sort == 'newest':
        base_qs = base_qs.order_by('-created_at')
    elif sort == 'oldest':
        base_qs = base_qs.order_by('created_at')
    
    all_products_qs = base_qs
    
    seven_days_ago = timezone.now() - timedelta(days=7)
    new_arrivals = all_products_qs.filter(created_at__gte=seven_days_ago)[:12]  # Limit featured
    
    paginator = Paginator(all_products_qs, 20)
    page = request.GET.get('page')
    all_products_page = paginator.get_page(page)
    
    categories_qs = Category.objects.filter(is_active=True).annotate(
        product_count=Count(
            'subcategories__products',
            filter=Q(subcategories__products__approval_status='APPROVED', subcategories__products__is_active=True),
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
        'total_products': all_products_page.paginator.count,
    }
    
    
    return render(request, 'core-templates/products.html', context)


def search_products(request):
    category_id = request.GET.get('category_id')
    sort = request.GET.get('sort', 'newest')
    query = request.GET.get('q', '').strip()

    base_qs = ProductVariant.objects.filter(
        product__approval_status='APPROVED',
        product__is_active=True,
        slug__isnull=False,
        slug__regex=r'^[-a-zA-Z0-9_]+$'
    ).select_related('product', 'product__subcategory__category').prefetch_related('images').annotate(
        avg_rating=Avg('product__reviews__rating'),
        review_count=Count('product__reviews', distinct=True),
        star_5=Count('product__reviews', filter=Q(product__reviews__rating=5), distinct=True),
        star_4=Count('product__reviews', filter=Q(product__reviews__rating=4), distinct=True),
        star_3=Count('product__reviews', filter=Q(product__reviews__rating=3), distinct=True),
        star_2=Count('product__reviews', filter=Q(product__reviews__rating=2), distinct=True),
        star_1=Count('product__reviews', filter=Q(product__reviews__rating=1), distinct=True)
    )

    if query:
        search_q = Q(product__name__icontains=query) | Q(product__description__icontains=query)
        base_qs = base_qs.filter(search_q)

    if category_id:
        base_qs = base_qs.filter(product__subcategory__category_id=category_id)
    
    if sort == 'price Asc':
        base_qs = base_qs.order_by('selling_price')
    elif sort == 'price_desc':
        base_qs = base_qs.order_by('-selling_price')
    elif sort == 'name_asc':
        base_qs = base_qs.order_by('product__name')
    elif sort == 'name_desc':
        base_qs = base_qs.order_by('-product__name')
    elif sort == 'newest':
        base_qs = base_qs.order_by('-created_at')
    elif sort == 'oldest':
        base_qs = base_qs.order_by('created_at')
    
    all_products_qs = base_qs
    
    seven_days_ago = timezone.now() - timedelta(days=7)
    new_arrivals = all_products_qs.filter(created_at__gte=seven_days_ago)[:12]
    
    paginator = Paginator(all_products_qs, 20)
    page = request.GET.get('page')
    all_products_page = paginator.get_page(page)
    
    categories_qs = Category.objects.filter(is_active=True).annotate(
        product_count=Count(
            'subcategories__products',
            filter=Q(subcategories__products__approval_status='APPROVED', subcategories__products__is_active=True),
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
        'total_products': all_products_page.paginator.count,
        'search_query': query,
        'is_search': True,
    }
    
    return render(request, 'core-templates/products.html', context)


def category_view(request, category_slug):

    category = get_object_or_404(Category, slug=category_slug, is_active=True)
    
    subcategories = SubCategory.objects.filter(category=category, is_active=True)
    
    subcategories_with_products = []
    
    for subcategory in subcategories:
        products = ProductVariant.objects.filter(
            product__subcategory=subcategory,
            product__approval_status='APPROVED',
            product__is_active=True
        ).select_related('product__subcategory__category').prefetch_related('images').annotate(
            avg_rating=Avg('product__reviews__rating'),
            review_count=Count('product__reviews', distinct=True),
            star_5=Count('product__reviews', filter=Q(product__reviews__rating=5), distinct=True),
            star_4=Count('product__reviews', filter=Q(product__reviews__rating=4), distinct=True),
            star_3=Count('product__reviews', filter=Q(product__reviews__rating=3), distinct=True),
            star_2=Count('product__reviews', filter=Q(product__reviews__rating=2), distinct=True),
            star_1=Count('product__reviews', filter=Q(product__reviews__rating=1), distinct=True)
        )[:5]
        
        total_products_count = ProductVariant.objects.filter(
            product__subcategory=subcategory,
            product__approval_status='APPROVED',
            product__is_active=True
        ).count()
        
        subcategories_with_products.append({
            'subcategory': subcategory,
            'products': list(products),
            'total_count': total_products_count
        })
    
    context = {
        'category': category,
        'subcategories_with_products': subcategories_with_products,
        'categories': Category.objects.filter(is_active=True)
    }
    
    if request.user.is_authenticated:
        context['data'] = request.user
    
    return render(request, 'core-templates/category-view.html', context)

def subcategory_products(request, category_slug, subcategory_slug):
    category = get_object_or_404(Category, slug=category_slug, is_active=True)
    subcategory = get_object_or_404(SubCategory, slug=subcategory_slug, category=category, is_active=True)
    
    products_qs = ProductVariant.objects.filter(
        product__subcategory=subcategory,
        product__approval_status='APPROVED',
        product__is_active=True
    ).select_related('product', 'product__subcategory', 'product__subcategory__category').prefetch_related('images').annotate(
        avg_rating=Avg('product__reviews__rating'),
        review_count=Count('product__reviews', distinct=True),
        star_5=Count('product__reviews', filter=Q(product__reviews__rating=5), distinct=True),
        star_4=Count('product__reviews', filter=Q(product__reviews__rating=4), distinct=True),
        star_3=Count('product__reviews', filter=Q(product__reviews__rating=3), distinct=True),
        star_2=Count('product__reviews', filter=Q(product__reviews__rating=2), distinct=True),
        star_1=Count('product__reviews', filter=Q(product__reviews__rating=1), distinct=True)
    )
    
    paginator = Paginator(products_qs, 20)
    page = request.GET.get('page')
    products_page = paginator.get_page(page)
    
    context = {
        'category': category,
        'subcategory': subcategory,
        'products_page': products_page,
        'categories': Category.objects.filter(is_active=True)
    }
    
    if request.user.is_authenticated:
        context['data'] = request.user
    
    return render(request, 'core-templates/subcategory-products.html', context)

def user_register(request):
    """Alias for register_view to maintain compatibility"""
    return register_view(request)

def register_view(request):
    if request.method == "POST":
        arrived_email = request.POST.get("email")
        arrived_username = request.POST.get("username")

        arrived_password = request.POST.get("password")

        arrived_confirm_password = request.POST.get("confirm_password")
        
        phone = request.POST.get('phone_number', '').strip()
        arrived_phone = phone if phone else None
        
        # Basic validation
        if User.objects.filter(email=arrived_email).exists():
            messages.error(request, 'Email already exists')
            return render(request, 'customer-templates/user_register.html', {'error_message': 'Email already exists'})
            
        if User.objects.filter(username=arrived_username).exists():

            messages.error(request, 'Username already exists')
            return render(request, 'customer-templates/user_register.html', {'error_message': 'Username already exists'})
        
        if arrived_phone and User.objects.filter(phone_number=arrived_phone).exists():
            messages.error(request, 'This phone number is already registered.')
            return render(request, 'customer-templates/user_register.html', {'error_message': 'Phone already registered'})
        
        if arrived_password != arrived_confirm_password:
            return render(request, 'customer-templates/user_register.html', {'error_message': 'Passwords do not match'})
        
        # Create inactive user
        user = User.objects.create_user(
            username=arrived_username,

            email=arrived_email,
            password=arrived_password
        )
        user.phone_number = arrived_phone
        user.save()
        
        # Generate and send OTP
        otp = generate_otp()
        request.session['email_otp'] = otp
        request.session['verify_user'] = str(user.id)
        
        send_otp_email(arrived_email, otp)
        
        messages.success(request, 'Registration successful! Please check your email for verification code.')
        return redirect("verify_email")
    
    return render(request, 'customer-templates/user_register.html')

def verify_email(request):
    if request.method == "POST":
        entered_otp = request.POST.get("otp")
        stored_otp = request.session.get("email_otp")
        user_id = request.session.get("verify_user")

        if entered_otp == stored_otp:
            user = User.objects.get(id=user_id)
            user.is_verified = True
            user.is_email_verified = True
            user.save()

            messages.success(request, "Email verified successfully")
            return redirect("login")

        else:
            messages.error(request, "Invalid OTP")

    return render(request, "core-templates/verify_email.html")

def user_login(request):
    error_msg = ''
    saved_username = ''
    if request.method == "POST":
        username_or_email = request.POST.get("username")
        password = request.POST.get("password")
        saved_username = username_or_email  
        
        try:
            user_obj = User.objects.get(email=username_or_email)
            username = user_obj.username
        except User.DoesNotExist:
            username = username_or_email
            
        data = authenticate(request, username=username, password=password)
        
        if data is not None:
            login(request, data)
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect("home")
        else:
            error_msg = "Invalid username/email or password"  

    return render(request, 'core-templates/login.html', {'error_message': error_msg, 'saved_username': saved_username})

def user_logout(request):
    logout(request)
    messages.error(request, 'Logout from account')
    return redirect('/')

@customer_required
def user_profile(request):
    user_data = request.user
    addresses = Address.objects.filter(user=request.user)
    
    if request.method == "POST":
        if 'update_details' in request.POST:
            first_name = request.POST.get('first_name', "").strip()
            last_name = request.POST.get('last_name', "").strip()
            arrived_phone = request.POST.get('phone_number', "").strip()
            
            if arrived_phone != "":
                phone_number = arrived_phone  
            else:
                phone_number = None
            
            if phone_number and User.objects.filter(phone_number=phone_number).exclude(id=user_data.id).exists():
                messages.error(request, 'This phone number is already registered.')
            else:
                user_data.first_name = first_name
                user_data.last_name = last_name
                user_data.phone_number = phone_number
                user_data.save()
                messages.success(request, 'Details updated successfully!')

        elif 'update_photo' in request.POST:
            image = request.FILES.get('image')
            if image:
                # SAFETY CHECK: Only delete if an old image actually exists
                if user_data.profile_image:
                    user_data.profile_image.delete(save=False)
                
                # Assign the new image and save to the database
                user_data.profile_image = image
                user_data.save()
                messages.success(request, 'Photo updated successfully!')
            else:
                messages.error(request, 'No image selected.')

        return redirect('profile') 
            
    return render(request, 'customer-templates/userprofile.html', {'data': user_data, 'addresses': addresses})


# @login_required
# def user_profile_image_update(request):
#     if request.method == "POST" and request.FILES.get('image'):
#         user = request.user
#         user.profile_image = request.FILES.get('image')
#         user.save()
#         messages.success(request, 'Profile photo updated successfully!')
#     return redirect('profile')

# @login_required
# def user_profile_update(request):
#     """Handles textual profile updates separately if needed."""
#     return redirect('profile')

@customer_required
def user_addresses(request):
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'customer-templates/useraddresses.html', {'addresses': addresses})

@customer_required
def user_address_adding(request):
    if request.method == "POST":
        address_obj = Address()
        
        address_obj.user = request.user
        address_obj.full_name = request.POST.get('full_name', '').strip().upper()
        address_obj.phone_number = request.POST.get('phone_number', '').strip()
        address_obj.pincode = request.POST.get('pincode', '').strip()
        address_obj.house_info = request.POST.get('house_info', '').strip().upper()
        address_obj.locality = request.POST.get('locality', '').strip().upper()
        address_obj.city = request.POST.get('city', '').strip().upper()
        address_obj.state = request.POST.get('state', '').strip().upper()
        address_obj.landmark = request.POST.get('landmark', '').strip().upper()
        address_obj.address_type = request.POST.get('address_type', 'HOME')
        
        is_default = request.POST.get('is_default') == 'on'
        
        if not Address.objects.filter(user=request.user).exists():
            is_default = True
            
        if is_default:
            Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
            
        address_obj.is_default = is_default
        
        address_obj.save()
        
        messages.success(request, "Address added successfully!")
        return redirect('user_addresses')

    return render(request, 'customer-templates/useradressadding.html')

@customer_required
def user_address_update(request, address_id):

    address = Address.objects.get(id=address_id, user=request.user)
    
    if request.method == "POST":
        address.full_name = request.POST.get('full_name', '').strip().upper()
        address.phone_number = request.POST.get('phone_number', '').strip()
        address.pincode = request.POST.get('pincode', '').strip()

        address.house_info = request.POST.get('house_info', '').strip().upper()
        address.locality = request.POST.get('locality', '').strip().upper()
        address.city = request.POST.get('city', '').strip().upper()
        address.state = request.POST.get('state', '').strip().upper()
        address.landmark = request.POST.get('landmark', '').strip().upper()
        address.address_type = request.POST.get('address_type', 'HOME')
        is_default = request.POST.get('is_default') == 'on'
        

        if is_default:

            Address.objects.filter(user=request.user, is_default=True).exclude(id=address_id).update(is_default=False)
            address.is_default = True
        else:

            if not Address.objects.filter(user=request.user).exclude(id=address_id).exists():
                address.is_default = True
            else:
                address.is_default = False

        address.save()
        
        messages.success(request, "Address updated successfully!")
        return redirect('user_addresses')

    return render(request, 'customer-templates/useraddressupdate.html', {'address': address})

@customer_required
def user_address_delete(request, address_id):
    address = Address.objects.get(id=address_id, user=request.user)
    
    was_default = address.is_default
    

    address.delete()
    
    if was_default:
        remaining_address = Address.objects.filter(user=request.user).first()
        if remaining_address:
            remaining_address.is_default = True
            remaining_address.save()
            messages.info(request, "Primary address deleted. A new default has been assigned.")
        else:
            messages.info(request, "Address deleted. You currently have no saved addresses.")
    else:
        messages.success(request, "Address removed successfully.")

    return redirect('user_addresses')

@customer_required
def user_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart).prefetch_related('variant__product', 'variant__images')
    for item in cart_items:
        item.item_total = item.quantity * item.price_at_time
    total_amount = sum(item.item_total for item in cart_items)
    
    return render(request, 'customer-templates/usercart.html', {
        'cart': cart_items,
        'total_amount': total_amount
    })

# @login_required
# def user_addto_cart(request, id):
#     user = request.user
#     cart, _ = Cart.objects.get_or_create(user=user)
#     product_variant = get_object_or_404(ProductVariant, id=id)
#     cart_item, created = CartItem.objects.get_or_create(
#         cart=cart, 
#         variant=product_variant, 
#         defaults={'price_at_time': product_variant.selling_price, 'quantity': 1}
#     )
    
#     if not created:
#         cart_item.quantity += 1
#         cart_item.price_at_time = product_variant.selling_price
#         cart_item.save()
    
#     # Get updated cart count (number of distinct items)
#     cart_count = CartItem.objects.filter(cart=cart).count()
    
#     # Check if it's an AJAX request
#     if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#         return JsonResponse({
#             'status': 'success',
#             'cart_count': cart_count,
#             'message': 'Item added to cart!'
#         })
    
#     return redirect('product_single', id=id)

# @login_required
# def cart_update_quantity(request, item_id, Asc action):
#     """AJAX view to update cart item Asc quantity (increase/decrease)"""
#     try:
#         cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        
#         if Asc action == 'increase':
#             cart_item.quantity += 1
#             cart_item.save()
            
#             # Calculate new total
#             cart_items = CartItem.objects.filter(cart=cart_item.cart)
#             total_amount = sum(item.quantity * item.price_at_time for item in cart_items)
#             cart_count = cart_items.count()
            
#             return JsonResponse({
#                 'status': 'success',
#                 'new_quantity': cart_item.quantity,
#                 'total_amount': f"{total_amount:.2f}",
#                 'item_total': f"{cart_item.quantity * cart_item.price_at_time:.2f}",
#                 'cart_count': cart_count
# Asc             })
            
#         elif action == 'decrease':
#             if cart_item.quantity > 1:
#                 cart_item Asc Asc .quantity -= 1
#                 cart_item.save()
                
#                 # Calculate new total
#                 cart_items = CartItem.objects.filter(cart=cart_item.cart)
#                 total_amount = sum(item.quantity * item.price_at_time for item in cart_items)
#                 cart_count = cart_items.count()
                
#                 return JsonResponse({
#                     'status': 'success',
#                     'new_quantity': cart_item.quantity,
#                     'total_amount': f"{total_amount:.2f}",
#                     'item_total': f"{cart_item Asc Asc .quantity * cart_item.price_at_time:.2f}",
#                     'cart_count': cart_count
#                 })
#             else:
#                 # If quantity is 1 and user clicks minus, delete the item
#                 cart = cart_item.cart
#                 cart_item.delete()
                
#                 # Get remaining item count and total
#                 remaining_items = CartItem.objects.filter(cart=cart)
#                 item_count = remaining_items.count()
#                 total_amount = sum(item.quantity * item.price_at_time for item in remaining_items)
                
#                 return JsonResponse({
#                     'status': 'success',
#                     'item_deleted': True,
#                     'cart_count': item_count,
#                     'total_amount': f"{total_amount:.2f}",
#                     'cart_empty': item_count == 0
# Asc                 })
        
#     except Exception Asc as e:
#         return JsonResponse({
#             'status': 'error',
#             'message': str(e)
# Asc         })

# @login_required
# def cart_remove_item(request, item_id):
# Asc Asc Asc """AJAX view to remove item from cart"""
# Asc Asc Asc try:
# Asc Asc Asc Asc Asc cart_item = get_object_or_404(CartItem, Asc id=item_id, cart__user=request.user)
# Asc Asc Asc Asc Asc cart = cart_item.cart
# Asc Asc Asc Asc Asc cart_item.delete()
        
# Asc Asc Asc Asc Asc Asc Asc # Get remaining item count and total
# Asc Asc Asc Asc Asc Asc Asc remaining_items = CartItem.objects.filter(cart=cart)
# Asc Asc Asc Asc Asc Asc Asc item_count = remaining_items.count()
# Asc Asc Asc Asc Asc Asc Asc total_amount = sum(item.quantity * item.price_at_time for item in remaining_items)
        
# Asc Asc Asc Asc Asc Asc Asc return JsonResponse({
# Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc 'status': 'success',
# Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc 'cart_count': item_count,
# Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc 'total_amount': f"{total_amount:.2f}",
# Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc 'cart_empty': item_count == 0
# Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc })
        
# Asc Asc Asc Asc Asc Asc except Exception as e:
# Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc return JsonResponse({
# Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc 'status': 'error',
# Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc 'message': str(e)
# Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc Asc })
    
@customer_required
def user_addto_cart(request, slug):
    if request.method == "POST":
        product_variant = get_object_or_404(ProductVariant, slug=slug)
        
        if product_variant.stock_quantity > 0:
            # Get quantity from POST, validate and default to 1
            quantity = 1
            try:
                qty = int(request.POST.get('quantity', 1))
                quantity = max(1, min(qty, product_variant.stock_quantity))
            except (ValueError, TypeError):
                quantity = 1
            
            cart, _ = Cart.objects.get_or_create(user=request.user)
            
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart, 
                variant=product_variant, 

                defaults={'price_at_time': product_variant.selling_price, 'quantity': quantity}
            )
            
            if not created:
                cart_item.quantity += quantity
                cart_item.price_at_time = product_variant.selling_price
                cart_item.save()
            
            messages.success(request, f"{quantity} x {product_variant.product.name} added to bag!")
        else:
            messages.error(request, "Sorry, this item is out of stock.")
            
    return redirect('product_single', slug=slug)



@customer_required
def cart_update_quantity(request, item_id, action):
    """Update cart item quantity (AJAX or form POST)"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    item_deleted = False
    previous_quantity = cart_item.quantity
    
    if action == 'increase':
        cart_item.quantity += 1
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
        else:
            cart = cart_item.cart
            cart_item.delete()
            item_deleted = True
    
    if not item_deleted:
        cart_item.save()
    
    # Calculate updated totals
    if item_deleted:
        cart = Cart.objects.get(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)
        total_amount = sum(item.quantity * item.price_at_time for item in cart_items)
        new_quantity = 0
        item_total = 0.0
    else:
        cart_items = CartItem.objects.filter(cart=cart_item.cart)
        total_amount = sum(item.quantity * item.price_at_time for item in cart_items)
        new_quantity = cart_item.quantity
        item_total = cart_item.quantity * cart_item.price_at_time
    
    if is_ajax:
        return JsonResponse({
            'status': 'success',
            'item_deleted': item_deleted,
            'new_quantity': new_quantity,
            'total_amount': float(total_amount),
            'item_total': float(item_total)
        })
    
    return redirect('cart')

@customer_required
def cart_remove_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    messages.info(request, "Item removed from cart.")
    return redirect('cart')

@customer_required
def user_wishlist(request):
    default_wishlist, _ = Wishlist.objects.get_or_create(user=request.user, wishlist_name=request.user.username)

    all_wishlists = Wishlist.objects.filter(user=request.user).order_by('-created_at')

    active_id = request.GET.get('id')
    if active_id:
        viewing_wishlist = get_object_or_404(Wishlist, id=active_id, user=request.user)
    else:
        viewing_wishlist = default_wishlist

    items = WishlistItem.objects.filter(wishlist=viewing_wishlist).prefetch_related(
        'variant__product__subcategory', 
        'variant__images'
    )

    return render(request, 'customer-templates/userwishlist.html', {
        'all_wishlists': all_wishlists,
        'active_wishlist': viewing_wishlist, 
        'items': items,
        'item_count': items.count(),
        'default_wishlist': default_wishlist,
    })

@customer_required
def set_active_wishlist(request):
    if request.method == "POST":
        wishlist_id = request.POST.get('wishlist_id')
        wishlist = get_object_or_404(Wishlist, id=wishlist_id, user=request.user)
        
        request.session['active_wishlist_id'] = str(wishlist.id)
        
        return JsonResponse({
            'status': 'success',
            'active_wishlist_name': wishlist.wishlist_name
        })
    return redirect('wishlist')

@customer_required
def create_wishlist(request):
    if request.method == "POST":
        name = request.POST.get('wishlist_name')
        if name:
            new_list = Wishlist.objects.create(user=request.user, wishlist_name=name)
            messages.success(request, f"Collection '{name}' created.")
            return redirect(f"/wishlist/?id={new_list.id}")
    return redirect('wishlist')

@customer_required
def rename_wishlist(request, wishlist_id):
    wishlist = get_object_or_404(Wishlist, id=wishlist_id, user=request.user)
    if request.method == "POST":
        new_name = request.POST.get('new_name')
        if new_name:
            wishlist.wishlist_name = new_name
            wishlist.save()
            messages.success(request, "Collection renamed.")
    return redirect(f"/wishlist/?id={wishlist.id}")

@customer_required
def delete_wishlist(request, wishlist_id):
    wishlist = get_object_or_404(Wishlist, id=wishlist_id, user=request.user)
    if wishlist.wishlist_name != request.user.username:

        wishlist.delete()
        # Reset session if deleted list was the active one
        if request.session.get('active_wishlist_id') == str(wishlist_id):
            request.session.pop('active_wishlist_id', None)
        messages.success(request, "Collection deleted.")
    return redirect('wishlist')

@customer_required
def remove_wishlist_item(request, item_id):
    item = get_object_or_404(WishlistItem, id=item_id, wishlist__user=request.user)
    wishlist_id = item.wishlist.id
    item.delete()
    return redirect(f"/wishlist/?id={wishlist_id}")

def toggle_wishlist_item(request, variant_slug):
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'unauthenticated',
            'message': 'You must be logged in to manage your wishlist.',
            'login_url': f"{reverse('login')}?next={request.path}"
        }, status=401)

    variant = get_object_or_404(ProductVariant, slug=variant_slug)
    
    # Get active wishlist
    active_wishlist_id = request.session.get('active_wishlist_id')
    all_wishlists = Wishlist.objects.filter(user=request.user)
    
    if active_wishlist_id:
        active_wishlist = all_wishlists.filter(id=active_wishlist_id).first()
    else:
        active_wishlist = all_wishlists.filter(wishlist_name=request.user.username).first()
    
    # If still no active wishlist, use the first one
    if not active_wishlist and all_wishlists.exists():
        active_wishlist = all_wishlists.first()
        request.session['active_wishlist_id'] = str(active_wishlist.id)
    
    if not active_wishlist:
        return JsonResponse({
            'status': 'error',
            'message': 'No wishlist found. Please create one.'
        })
    
    # Check if item already exists in wishlist
    existing_item = WishlistItem.objects.filter(wishlist=active_wishlist, variant=variant).first()

    
    if existing_item:
        existing_item.delete()
        is_in_wishlist = False
        message = 'Removed from wishlist'
    else:
        WishlistItem.objects.create(wishlist=active_wishlist, variant=variant)
        is_in_wishlist = True
        message = 'Added to wishlist'
    
    return JsonResponse({
        'status': 'success',
        'is_in_wishlist': is_in_wishlist,
        'message': message
    })

@customer_required
def user_checkout(request):
    cart = Cart.objects.filter(user=request.user).first()
    
    # Handle single product buy now via GET param (fallback for direct access)
    single_slug = request.GET.get('single')
    if single_slug and not cart.items.exists():
        from core.views import single_product_checkout
        return single_product_checkout(request, single_slug)
    
    if not cart or not cart.items.exists():
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart')
    
    cart_items = cart.items.select_related('variant__product').prefetch_related('variant__images')
    for item in cart_items:
        item.item_total = item.quantity * item.price_at_time
    total_amount = sum(item.item_total for item in cart_items)
    
    addresses = Address.objects.filter(user=request.user)
    if not addresses.exists():
        messages.info(request, 'Please add a shipping address first.')
    
    # Detect single checkout and back product
    is_single_checkout = request.session.get('single_checkout', False)
    back_product_slug = request.session.get('checkout_back_product')
    
    if is_single_checkout:
        # Clear the flag after use
        request.session.pop('single_checkout', None)
        # Don't clear back_product_slug here - let checkout_process clear it
    
    return render(request, 'customer-templates/usercheckout.html', {
        'addresses': addresses,
        'cart_data': cart_items,
        'total_amount': total_amount,
        'cart': cart,
        'is_single_checkout': is_single_checkout,
        'back_product_slug': back_product_slug
    })

@customer_required
def user_checkout_process(request):
    if request.method != 'POST':
        return redirect('checkout')
    
    cart = Cart.objects.filter(user=request.user).first()
    if not cart or not cart.items.exists():
        messages.error(request, 'Cannot process empty cart.')
        return redirect('cart')
    
    try:
        selected_address_id = request.POST.get('selected_address')
        payment_method = request.POST.get('payment_method')
        
        # Fix payment status mapping
        display_payment = payment_method.upper() if payment_method == 'online' else 'COD'
        
        if not selected_address_id or payment_method not in ['online', 'cod']:
            messages.error(request, 'Please select address and payment method.')
            return redirect('checkout')
        
        address = get_object_or_404(Address, id=selected_address_id, user=request.user)
        
        # Calculate final total
        cart_items = cart.items.select_related('variant__product')
        total_amount = sum(item.quantity * Decimal(str(item.price_at_time)) for item in cart_items)
        
        # Generate unique order number
        import uuid
        order_number = f"CS-{uuid.uuid4().hex.upper()[:8]}"
        
        # Create Order
        order = Order.objects.create(
            user=request.user,
            order_number=order_number,
            total_amount=total_amount,
            payment_status=display_payment,
            order_status='placed'
        )
        order.shipping_address = address
        order.save()
        
        # Create OrderItems + update stock
        for cart_item in cart_items:
            variant = cart_item.variant
            if variant.stock_quantity >= cart_item.quantity:

                OrderItem.objects.create(
                    order=order,
                    variant=variant,
                    seller=variant.product.seller,
                    quantity=cart_item.quantity,
                    price_at_purchase=cart_item.price_at_time
                )
                # Update stock
                variant.stock_quantity -= cart_item.quantity
                variant.save()
            else:
                messages.warning(request, f'Insufficient stock for {variant.sku_code}. Item skipped.')
        
        # Clear cart + session flags
        cart.items.all().delete()
        request.session.pop('checkout_back_product', None)
        request.session.pop('single_checkout', None)
        request.session.modified = True
        
        messages.success(request, f'Order #{order_number} placed successfully!')
        return redirect('order_success', order_id=order.id)
        
    except Exception as e:
        messages.error(request, 'Order processing failed. Please try again.')
        return redirect('checkout')

@customer_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.items.select_related('variant__product').prefetch_related('variant__images')
    return render(request, 'customer-templates/order-success.html', {
        'order': order,
        'order_items': order_items
    })

@customer_required
def user_orders(request):
    orders = Order.objects.filter(
        user=request.user
    ).prefetch_related(
        'items__variant__product',
        'items__variant__images'
    ).order_by('-ordered_at')
    return render(request, 'customer-templates/userorders.html', {'orders': orders})

@customer_required
def user_track(request, order_id):
    return render(request, 'customer-templates/usertrack.html', {'order_id': order_id})

@customer_required
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related(
            'items__variant__product',
            'items__variant__images'
        ).select_related('shipping_address'),
        id=order_id,
        user=request.user
    )
    context = {
        'order': order,
        'order_items': order.items.all(),
        'order_status_display': order.order_status.replace('_', ' ').title()
    }
    

    # Add review eligibility for delivered orders with review status
    eligible_items = []
    review_status = {}
    if order.order_status == 'delivered':
        eligible_items = order.items.all()
        # Get user's existing reviews for products in this order
        product_ids = [item.variant.product.id for item in eligible_items]
        user_reviews = Review.objects.filter(
            user=request.user,
            product_id__in=product_ids
        )
    review_status_list = [(review.product_id, review) for review in user_reviews]
    context['eligible_items'] = eligible_items
    context['review_status_list'] = review_status_list

    
    return render(request, 'customer-templates/order-detail.html', context)

@customer_required
def my_reviews(request):
    reviews = Review.objects.filter(
        user=request.user
).select_related('product').prefetch_related('product__variants__images').order_by('-created_at')
    
    paginator = Paginator(reviews, 10)
    page = request.GET.get('page')
    reviews_page = paginator.get_page(page)
    
    context = {
        'reviews_page': reviews_page,
        'total_reviews': reviews.count()
    }
    return render(request, 'customer-templates/my-reviews.html', context)

@customer_required
def submit_review(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        order_id = request.POST.get('order_id')
        rating = int(request.POST.get('rating', 0))
        comment = request.POST.get('comment', '').strip()
        
        if not product_id or not order_id or rating < 1 or rating > 5:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': 'Invalid input'})
            messages.error(request, 'Invalid input')
            return redirect('order_detail', order_id=order_id)
        
        product = get_object_or_404(Product, id=product_id)
        order = get_object_or_404(Order, id=order_id, user=request.user)
        
        review, created = Review.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={'rating': rating, 'comment': comment}
        )
        
        if not created:
            review.rating = rating
            review.comment = comment
            review.is_edited = True
            review.save()
        
        messages.success(request, f"{'Review created' if created else 'Review updated'} successfully!")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': 'Review submitted/updated!',
                'created': created
            })
    
    return redirect('order_detail', order_id=order_id)


@customer_required
def edit_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    product = review.product
    
    if request.method == 'POST':
        rating = int(request.POST.get('rating', 0))
        comment = request.POST.get('comment', '').strip()
        
        if 1 <= rating <= 5:
            review.rating = rating
            review.comment = comment
            review.is_edited = True
            review.save()
            messages.success(request, 'Review updated successfully!')
            return redirect('my_reviews')
        else:
            messages.error(request, 'Rating must be between 1 and 5 stars.')
    
    context = {
        'review': review,
        'product': product,
    }
    return render(request, 'customer-templates/edit-review.html', context)

# Create your views here.
