from django.shortcuts import render, redirect
from django.contrib import messages
from seller.models import Product, ProductVariant, ProductImage
from customer.models import *
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Avg, Count, Q
from customer.models import Review


def login_view(request):
    return render(request, 'login.html')

# def main_home(request):
#     # Get approved and active products with their first variant's price
#     products = Product.objects.filter(
#         approval_status='APPROVED',
#         is_active=True
#     ).select_related('subcategory', 'seller').prefetch_related('variants')[:12]
    
#     return render(request, 'mainhome.html', {'products': products})

def order_details(request):
    return render(request, 'orderdetails.html')


def product_single(request, slug):
    product = get_object_or_404(ProductVariant.objects.select_related('product').prefetch_related('images'), slug=slug)
    
    cart_count = 0
    is_in_cart = False
    all_wishlists = []
    active_wishlist_id = None
    active_wishlist = None
    is_in_wishlist = False
    
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_count = CartItem.objects.filter(cart=cart).count()
            is_in_cart = CartItem.objects.filter(cart=cart, variant=product).exists()
        except Cart.DoesNotExist:
            cart_count = 0
    
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_count = CartItem.objects.filter(cart=cart).count()
        except Cart.DoesNotExist:
            cart_count = 0
        
        # Get all user's wishlists
        all_wishlists = Wishlist.objects.filter(user=request.user).order_by('-created_at')
        
        # Get active wishlist from session or use default
        active_wishlist_id = request.session.get('active_wishlist_id')
        
        if active_wishlist_id:
            # Verify the wishlist belongs to this user
            active_wishlist = all_wishlists.filter(id=active_wishlist_id).first()
            if not active_wishlist:
                # Invalid wishlist ID, use default
                active_wishlist = all_wishlists.filter(wishlist_name=request.user.username).first()
        else:
            # Default to username-based wishlist
            active_wishlist = all_wishlists.filter(wishlist_name=request.user.username).first()
        
        # If still no active wishlist, use the first one
        if not active_wishlist and all_wishlists.exists():
            active_wishlist = all_wishlists.first()
            request.session['active_wishlist_id'] = str(active_wishlist.id)
        
        # Check if product is in active wishlist
        if active_wishlist:
            active_wishlist_id = active_wishlist.id
            is_in_wishlist = WishlistItem.objects.filter(
                wishlist=active_wishlist, 
                variant=product
            ).exists()
    
    # Reviews section
    # Reviews
    reviews = product.product.reviews.select_related('user').prefetch_related('images').order_by('-created_at')[:12]
    avg_result = reviews.aggregate(avg_rating=Avg('rating'))
    avg_rating = avg_result['avg_rating'] or 0
    review_count = reviews.count()
    
    # Rating distribution
    rating_distribution = product.product.reviews.aggregate(
        star_5=Count('id', filter=Q(rating=5)),
        star_4=Count('id', filter=Q(rating=4)),
        star_3=Count('id', filter=Q(rating=3)),
        star_2=Count('id', filter=Q(rating=2)),
        star_1=Count('id', filter=Q(rating=1))
    )
    rating_distribution = [
        {'rating': 5, 'count': rating_distribution['star_5'] or 0},
        {'rating': 4, 'count': rating_distribution['star_4'] or 0},
        {'rating': 3, 'count': rating_distribution['star_3'] or 0},
        {'rating': 2, 'count': rating_distribution['star_2'] or 0},
        {'rating': 1, 'count': rating_distribution['star_1'] or 0},
    ]
    
    # Related products (same subcategory, exclude self)
    related_products = ProductVariant.objects.filter(
        product__subcategory=product.product.subcategory,
        product__approval_status='APPROVED',
        product__is_active=True
    ).exclude(product=product.product).select_related('product').prefetch_related('images')[:4]
    
    return render(request, 'core-templates/productsingle.html', {
        "data": product, 
        'cart_count': cart_count,
        'all_wishlists': all_wishlists,
        'active_wishlist_id': active_wishlist_id,
        'active_wishlist_name': active_wishlist.wishlist_name if active_wishlist else request.user.username,
        'is_in_wishlist': is_in_wishlist,
        'is_in_cart': is_in_cart,
        'reviews': reviews,
        'avg_rating': round(float(avg_rating), 1),
        'review_count': review_count,
        'rating_distribution': rating_distribution,
        'related_products': related_products
    })

    
def helpe_center(request):
    return render(request, 'core-templates/helpe_center.html')

def support_or_contact(request):
    return render(request, 'core-templates/Support_or_contact.html')

def about(request):
    return render(request, 'core-templates/about.html')

def shipping_info(request):
    return render(request, 'core-templates/shippinginfo.html')

@login_required(login_url='login')
def buy_again(request, order_id, item_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    item = get_object_or_404(OrderItem, id=item_id, order=order)
    
    if request.method == 'POST':
        if item.variant.stock_quantity <= 0:
            messages.error(request, "Sorry, this item is out of stock.")
            return redirect('buy_again', order_id=order.id, item_id=item.id)
            
        try:
            qty = int(request.POST.get('quantity', 1))
            quantity = max(1, min(qty, item.variant.stock_quantity, 3))
        except (ValueError, TypeError):
            quantity = 1
            
        cart, _ = Cart.objects.get_or_create(user=request.user)
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, 
            variant=item.variant, 
            defaults={'price_at_time': item.variant.selling_price, 'quantity': quantity}
        )
        
        if not created:
            total_quantity = cart_item.quantity + quantity
            if total_quantity > min(3, item.variant.stock_quantity):
                cart_item.quantity = min(3, item.variant.stock_quantity)
                messages.warning(request, f"You can only order up to {cart_item.quantity} of this product.")
            else:
                cart_item.quantity = total_quantity
                messages.success(request, f"{quantity} x {item.variant.product.name} added to bag!")
            cart_item.price_at_time = item.variant.selling_price
            cart_item.save()
        else:
            messages.success(request, f"{quantity} x {item.variant.product.name} added to bag!")
            
        return redirect('cart')

    # Calculate the remaining allowed quantity (Max 3 per purchase)
    cart = Cart.objects.filter(user=request.user).first()
    existing_qty = 0
    if cart:
        cart_item = cart.items.filter(variant=item.variant).first()
        if cart_item:
            existing_qty = cart_item.quantity

    return render(request, 'core-templates/buyagain.html', {
        'order': order,
        'item': item,
        'variant': item.variant,
        'available_quantity': max(0, min(3, item.variant.stock_quantity) - existing_qty)
    })


def privacypolicy(request):
    return render(request, 'core-templates/privacypolicy_and_termsandconditions.html')

# Deprecated - Buy Now now handled in customer.views.buy_now_checkout
# @login_required
# def single_product_checkout(request, slug):
#     pass
