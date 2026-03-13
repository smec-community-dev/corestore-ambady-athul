from django.shortcuts import render,redirect,get_object_or_404
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import *
from core.models import *
from seller.models import *
from django.contrib.auth import login,logout,authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F, Q, Count
from decimal import Decimal

from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta

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
    from django.db.models import Count
    
    category_id = request.GET.get('category_id')
    sort = request.GET.get('sort', 'newest')
    
    base_qs = ProductVariant.objects.filter(product__approval_status='APPROVED',product__is_active=True).select_related('product', 'product__subcategory__category').prefetch_related('images')
    
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
    
    # New arrivals (filtered/sorted same way, last 7 days)
    seven_days_ago = timezone.now() - timedelta(days=7)
    new_arrivals = all_products_qs.filter(created_at__gte=seven_days_ago)[:12]  # Limit featured
    
    # Paginate all_products
    paginator = Paginator(all_products_qs, 20)
    page = request.GET.get('page')
    all_products_page = paginator.get_page(page)
    
# Categories with product counts for sidebar - ALL active categories
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
    
    if request.user.is_authenticated:
        context['data'] = request.user
    
    return render(request, 'core-templates/products.html', context)

def category_view(request, category_slug):
    """View to display subcategories and products when a category is clicked"""
    category = get_object_or_404(Category, slug=category_slug, is_active=True)
    
    # Get active subcategories for this category
    subcategories = SubCategory.objects.filter(category=category, is_active=True)
    
    # Build context with subcategories and their products (max 5 per subcategory)
    subcategories_with_products = []
    
    for subcategory in subcategories:
        # Get approved and active products for this subcategory (max 5)
        # Include products even with 0 stock to display them (OOS badge will show)
        products = ProductVariant.objects.filter(
            product__subcategory=subcategory,
            product__approval_status='APPROVED',
            product__is_active=True
        ).select_related('product__subcategory__category').prefetch_related('images')[:5]
        
        # Get total product count for "Show All" button
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
    """View to display all products for a specific subcategory"""
    category = get_object_or_404(Category, slug=category_slug, is_active=True)
    subcategory = get_object_or_404(SubCategory, slug=subcategory_slug, category=category, is_active=True)
    
    # Get all approved and active products for this subcategory
    products_qs = ProductVariant.objects.filter(
        product__subcategory=subcategory,
        product__approval_status='APPROVED',
        product__is_active=True
    ).select_related('product', 'product__subcategory', 'product__subcategory__category').prefetch_related('images')
    
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
    error_msg = ''
    saved_data = {'username': '', 'email': '', 'phone_number': ''}
    if request.method == 'POST':
        # user_obj = User()
        # user_obj.phone_number = request.POST.get('phone_number') 
        # # user_obj.email = request.POST.get('email') 
        # arrived_email = request.POST.get('email') 
        # # user_obj.username = request.POST.get('username')
        # arrived_username = request.POST.get('username')
        # arrived_password = request.POST.get('password') 
        # arrived_confirm_password = request.POST.get('confirm_password')
        # allready_exist_email = authenticate(request, email = arrived_email)
        # allready_exist_username = authenticate(request, username = arrived_username)
        # if allready_exist_email is not None:
        #     messages.error(request,'Email already exist')
        #     return redirect('register')
        # if allready_exist_username is not None:
        #     messages.error(request,'Username already exist')
        #     return redirect('register')
        arrived_username = request.POST.get('username')
        arrived_email = request.POST.get('email')
        arrived_password = request.POST.get('password') 
        arrived_confirm_password = request.POST.get('confirm_password')
        
        phone = request.POST.get('phone_number', '').strip()
        arrived_phone = phone if phone else None
        
        # Save data for repopulating form on error
        saved_data = {
            'username': arrived_username,
            'email': arrived_email,
            'phone_number': arrived_phone
        }
        
        if User.objects.filter(email=arrived_email).exists():
            messages.error(request, 'Email already exists')
            return redirect('register')
            
        if User.objects.filter(username=arrived_username).exists():
            messages.error(request, 'Username already exists')
            return redirect('register')
        
        if arrived_phone and User.objects.filter(phone_number=arrived_phone).exists():
            messages.error(request, 'This phone number is already registered.')
            return redirect('register')
        
        if arrived_password == arrived_confirm_password :
            user_obj = User.objects.create_user(
                username=arrived_username,
                email=arrived_email,
                password=arrived_password,
            )
            user_obj.phone_number = arrived_phone
            user_obj.save()
            
            messages.success(request, 'Registration successful! Please login.')
            return redirect('login') 
        else:
            error_msg = "Entered a different password."
    return render(request, 'customer-templates/user_register.html', {'error_message': error_msg, 'saved_data': saved_data})

def user_login(request):
    error_msg = ''
    saved_username = ''
    if request.method == "POST":
        username_or_email = request.POST.get("username")
        password = request.POST.get("password")
        saved_username = username_or_email  # Save for repopulating on error
        
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

@login_required
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
                user_data.profile_image = image
                user_data.save()
                messages.success(request, 'Photo updated successfully!')
            else:
                messages.error(request, 'No image selected.')

        return redirect('profile') 
            
    return render(request, 'customer-templates/userprofile.html', {'data': user_data,'addresses': addresses})


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

@login_required
def user_addresses(request):
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'customer-templates/useraddresses.html', {'addresses': addresses})

@login_required
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

@login_required
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

@login_required
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

@login_required
def user_cart(request):
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = CartItem.objects.filter(cart=cart).prefetch_related('variant__product', 'variant__images')
    
    # for item in cart_items:
    total_amount = sum(item.quantity * item.price_at_time for item in cart_items)
    
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
# def cart_update_quantity(request, item_id, action):
#     """AJAX view to update cart item quantity (increase/decrease)"""
#     try:
#         cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        
#         if action == 'increase':
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
#             })
            
#         elif action == 'decrease':
#             if cart_item.quantity > 1:
#                 cart_item.quantity -= 1
#                 cart_item.save()
                
#                 # Calculate new total
#                 cart_items = CartItem.objects.filter(cart=cart_item.cart)
#                 total_amount = sum(item.quantity * item.price_at_time for item in cart_items)
#                 cart_count = cart_items.count()
                
#                 return JsonResponse({
#                     'status': 'success',
#                     'new_quantity': cart_item.quantity,
#                     'total_amount': f"{total_amount:.2f}",
#                     'item_total': f"{cart_item.quantity * cart_item.price_at_time:.2f}",
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
#                 })
        
#     except Exception as e:
#         return JsonResponse({
#             'status': 'error',
#             'message': str(e)
#         })

# @login_required
# def cart_remove_item(request, item_id):
#     """AJAX view to remove item from cart"""
#     try:
#         cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
#         cart = cart_item.cart
#         cart_item.delete()
        
#         # Get remaining item count and total
#         remaining_items = CartItem.objects.filter(cart=cart)
#         item_count = remaining_items.count()
#         total_amount = sum(item.quantity * item.price_at_time for item in remaining_items)
        
#         return JsonResponse({
#             'status': 'success',
#             'cart_count': item_count,
#             'total_amount': f"{total_amount:.2f}",
#             'cart_empty': item_count == 0
#         })
        
#     except Exception as e:
#         return JsonResponse({
#             'status': 'error',
#             'message': str(e)
#         })

@login_required
def user_addto_cart(request, slug):
    if request.method == "POST":
        product_variant = get_object_or_404(ProductVariant, slug=slug)
        
        if product_variant.stock_quantity > 0:
            cart, _ = Cart.objects.get_or_create(user=request.user)
            
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart, 
                variant=product_variant, 
                defaults={'price_at_time': product_variant.selling_price, 'quantity': 1}
            )
            
            if not created:
                cart_item.quantity += 1
                cart_item.price_at_time = product_variant.selling_price
                cart_item.save()
            
            messages.success(request, f"{product_variant.product.name} added to bag!")
        else:
            messages.error(request, "Sorry, this item is out of stock.")
            
    return redirect('product_single', slug=slug)



@login_required
def cart_update_quantity(request, item_id, action):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    
    if action == 'increase':
        cart_item.quantity += 1
        cart_item.save()
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
            messages.info(request, "Item removed from cart.")
            
    return redirect('cart')

@login_required
def cart_remove_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    messages.info(request, "Item removed from cart.")
    return redirect('cart')

@login_required
def user_wishlist(request):
    default_wishlist, _ = Wishlist.objects.get_or_create(user=request.user, wishlist_name=request.user.username)

    all_wishlists = Wishlist.objects.filter(user=request.user).order_by('-created_at')

    #Determine which wishlist to VIEW (GET param)
    active_id = request.GET.get('id')
    if active_id:
        viewing_wishlist = get_object_or_404(Wishlist, id=active_id, user=request.user)
    else:
        viewing_wishlist = default_wishlist

    # Fetch items for the list we are looking at
    items = WishlistItem.objects.filter(wishlist=viewing_wishlist).prefetch_related(
        'variant__product__subcategory', 
        'variant__images'
    )

    return render(request, 'customer-templates/userwishlist.html', {
        'all_wishlists': all_wishlists,
        'active_wishlist': viewing_wishlist, # The one being viewed
        'items': items,
        'item_count': items.count(),
        'default_wishlist': default_wishlist,
    })

@login_required
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

@login_required
def create_wishlist(request):
    if request.method == "POST":
        name = request.POST.get('wishlist_name')
        if name:
            new_list = Wishlist.objects.create(user=request.user, wishlist_name=name)
            messages.success(request, f"Collection '{name}' created.")
            return redirect(f"/wishlist/?id={new_list.id}")
    return redirect('wishlist')

@login_required
def rename_wishlist(request, wishlist_id):
    wishlist = get_object_or_404(Wishlist, id=wishlist_id, user=request.user)
    if request.method == "POST":
        new_name = request.POST.get('new_name')
        if new_name:
            wishlist.wishlist_name = new_name
            wishlist.save()
            messages.success(request, "Collection renamed.")
    return redirect(f"/wishlist/?id={wishlist.id}")

@login_required
def delete_wishlist(request, wishlist_id):
    wishlist = get_object_or_404(Wishlist, id=wishlist_id, user=request.user)
    if wishlist.wishlist_name != request.user.username:
        wishlist.delete()
        # Reset session if deleted list was the active one
        if request.session.get('active_wishlist_id') == str(wishlist_id):
            request.session.pop('active_wishlist_id', None)
        messages.success(request, "Collection deleted.")
    return redirect('wishlist')

@login_required
def remove_wishlist_item(request, item_id):
    item = get_object_or_404(WishlistItem, id=item_id, wishlist__user=request.user)
    wishlist_id = item.wishlist.id
    item.delete()
    return redirect(f"/wishlist/?id={wishlist_id}")

@login_required
def toggle_wishlist_item(request, variant_slug):
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

@login_required
def user_checkout(request):
    addresses = Address.objects.filter(user = request.user)
    return render(request, 'customer-templates/usercheckout.html',{'address':addresses})

@login_required
def user_orders(request):
    return render(request, 'customer-templates/userorders.html')

@login_required
def user_track(request, order_id):
    return render(request, 'customer-templates/usertrack.html', {'order_id': order_id})





# Create your views here.
