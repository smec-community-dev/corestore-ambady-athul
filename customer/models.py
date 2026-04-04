import uuid
from django.db import models

class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField("core.User", on_delete=models.CASCADE, related_name="cart")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Cart: {self.user.username}"

class CartItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey("seller.ProductVariant", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price_at_time = models.FloatField(null=True,default=0.0)
    
    def __str__(self):
        return f"{self.variant.sku_code} x {self.quantity}"

class Wishlist(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey("core.User", on_delete=models.CASCADE, related_name="wishlists")
    wishlist_name = models.CharField(max_length=100, default="My Wishlist")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.wishlist_name

class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey("seller.ProductVariant", on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

class Review(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey("core.User", on_delete=models.CASCADE)
    product = models.ForeignKey("seller.Product", on_delete=models.CASCADE, related_name="reviews")
    rating = models.IntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_edited = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('user', 'product')
    
    def __str__(self):
        return f"Review by {self.user.username}"

class ReviewImage(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='review_images/', null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review image for {self.review.user.username} - {self.review.product.name}"

class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey("core.User", on_delete=models.CASCADE, related_name="orders", null=True, blank=True)
    order_number = models.CharField(max_length=100, unique=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, default='PENDING')
    order_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('placed', 'Placed'),
            ('processing', 'Processing'),
            ('shipped', 'Shipped'),
            ('delivered', 'Delivered'),
            ('cancelled', 'Cancelled'),
        ],
        default="placed"
    )
    ordered_at = models.DateTimeField(auto_now_add=True)
    shipping_address = models.ForeignKey("core.Address", on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")
    cancel_reason = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.order_number

class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey("seller.ProductVariant", on_delete=models.CASCADE)
    seller = models.ForeignKey("seller.SellerProfile", on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)
    
    @property
    def subtotal(self):
        return self.quantity * self.price_at_purchase

    def __str__(self):
        return f"{self.variant.sku_code} (Order {self.order.order_number})"