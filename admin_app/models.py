import uuid
from django.db import models

class Offer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title

class Discount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    discount_type = models.CharField(max_length=20, choices=(('PERCENTAGE', 'Percentage'), ('FLAT', 'Flat Amount')))
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return self.name

class Coupon(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    usage_limit = models.IntegerField()
    used_count = models.IntegerField(default=0)
    
    def __str__(self):
        return self.code

class OfferDiscountBridge(models.Model):
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE  ,null=True,blank=True)

    discount = models.ForeignKey(Discount, on_delete=models.CASCADE  ,null=True,blank=True)

    
    def __str__(self):
        return f"{self.offer.title} - {self.discount.name}"

class ProductOfferBridge(models.Model):
    product = models.ForeignKey("seller.Product", on_delete=models.CASCADE  ,null=True,blank=True)

    offer = models.ForeignKey(Offer, on_delete=models.CASCADE  ,null=True,blank=True)

    
    def __str__(self):
        return f"{self.product.name} - {self.offer.title}"

class CategoryOfferBridge(models.Model):
    category = models.ForeignKey("core.Category", on_delete=models.CASCADE  ,null=True,blank=True)

    offer = models.ForeignKey(Offer, on_delete=models.CASCADE  ,null=True,blank=True)


class ProductDiscountBridge(models.Model):
    product = models.ForeignKey("seller.Product", on_delete=models.CASCADE  ,null=True,blank=True)
    discount = models.ForeignKey(Discount, on_delete=models.CASCADE ,null=True,blank=True)

class CategoryDiscountBridge(models.Model):
    category = models.ForeignKey("core.Category", on_delete=models.CASCADE)
    discount = models.ForeignKey(Discount, on_delete=models.CASCADE)

class PlatformCommission(models.Model):
    seller = models.ForeignKey(
        "seller.SellerProfile",
        on_delete=models.CASCADE,
        null=True,        
        blank=True        
    )
    order_item = models.ForeignKey(
        "customer.OrderItem",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    commission_percentage = models.FloatField()
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2)
    settlement_status = models.CharField(max_length=20, default='UNSETTLED')
    settled_at = models.DateTimeField(null=True, blank=True)