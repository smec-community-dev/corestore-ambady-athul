from django.shortcuts import render,redirect
from django.http import HttpResponse
from core.models import User,Category,SubCategory
from .models import SellerProfile,Product,ProductVariant,ProductImage,Attribute,AttributeOption,VariantAttributeBridge,ReturnRequest
from customer.models import OrderItem,Order
from django.utils.text import slugify
from django.contrib.auth import authenticate, login ,logout
from core.decorator import seller_required
from django.contrib import messages




def selleregis(request):
    if request.method=="POST":
        username=request.POST.get("username")
        password=request.POST.get("password")
        email=request.POST.get("email")
        data=User.objects.filter(username=username,email=email)
        if data:
            return HttpResponse("user already exist")
        else:
            user=User.objects.create_user(username=username,
                                          password=password,
                                          email=email,
                                          first_name=request.POST.get("first_name"),
                                          last_name=request.POST.get("last_name"),
                                          phone_number=request.POST.get("phone_number"),
                                          role="SELLER",
                                          profile_image=request.FILES.get("profile_image"),
                                          )
            
            sellr=SellerProfile.objects.create( user=user,
                                                store_name=request.POST.get("store_name"),
                                                store_slug=slugify(request.POST.get("store_name")),
                                                gst_number=request.POST.get("gst_number"),
                                                pan_number=request.POST.get("pan_number"),
                                                bank_account_number=request.POST.get("bank_account_number"),
                                                ifsc_code=request.POST.get("ifsc_code"),
                                                business_address=request.POST.get("business_address"),
                                                )
            
            return redirect("/login/")
    return render(request,"seller/sellerregistration.html")

def sellerlogin(request):
    if request.method=="POST":
        username=request.POST.get("username")
        password=request.POST.get("password")
        data=authenticate(request,username=username,password=password)
        if data:
            if data.role =="SELLER":
                login(request,data)
                return redirect("/sellerhome/")
                
            else:
                messages.error(request,"invalid username or password")
        else:
            return redirect("/regis/")    
    return render(request,"seller/sellerlogin.html")


@seller_required
def sellerhome(request):
    seller=SellerProfile.objects.get(user=request.user)
    products=(Product.objects.filter(seller=seller,is_active=True).prefetch_related("variants__images").order_by("-created_at"))
    return render(request, "seller/sellerhome.html", {"products": products,"seller":seller})


@seller_required
def sellerprofile(request):
    data=request.user
    datas=SellerProfile.objects.get(user=data)
    return render(request,"seller/sellerprofile.html",{"datas":datas})

def seller_logout(request):
    logout(request)
    return redirect('/login/')

@seller_required
def sellerproduct(request):
    sub=SubCategory.objects.all()
    if request.method=="POST":
        # data=Product()
        # datas=ProductVariant()
        m=SubCategory.objects.get(id=request.POST.get("subcategory"))
        data=Product.objects.create(
            seller=SellerProfile.objects.get(user=request.user),
            subcategory=m,
            name=request.POST.get("name"),
            description=request.POST.get("description"),
            brand=request.POST.get("brand"),
            model_number=request.POST.get("model_number"),
            return_days=request.POST.get("return_days"),
            # approval_status=request.POST.get("approval_status"),
            is_cancellable=bool(request.POST.get("is_cancellable")) ,
            is_returnable=bool(request.POST.get("is_returnable")), 
            )
        
        datas=ProductVariant.objects.create(
            product=data,
            sku_code=request.POST.get("sku_code"),
            mrp=request.POST.get("mrp"),
            selling_price=request.POST.get("selling_price"),
            cost_price=request.POST.get("cost_price"),
            stock_quantity=request.POST.get("stock_quantity"),
            weight=request.POST.get("weight"),
            length=request.POST.get("length"),
            width=request.POST.get("width"),
            height=request.POST.get("height"),
            tax_percentage=request.POST.get("tax_percentage"),
        )
        
        return redirect("/sellerhome/")

    return render(request,"seller/sellerproduct.html",{"sub":sub})    

@seller_required
def sellerproduct_update(request, id):
    sub = SubCategory.objects.all()
    product = Product.objects.get(id=id)
    variant = ProductVariant.objects.get(product=product)
    if request.method == "POST":
        product.seller=SellerProfile.objects.get(user=request.user)
        m=SubCategory.objects.get(id=request.POST.get("subcategory"))
        product.subcategory=m
        product.name=request.POST.get("name")
        product.slug=request.POST.get("slug")
        product.description=request.POST.get("description")
        product.brand=request.POST.get("brand")
        product.model_number=request.POST.get("model_number")
        product.return_days=request.POST.get("return_days")
        product.approval_status=request.POST.get("approval_status")
        product.is_cancellable=bool(request.POST.get("is_cancellable")) 
        product.is_returnable=bool(request.POST.get("is_returnable")) 
        product.save()
        variant.product=product
        variant.sku_code=request.POST.get("sku_code")
        variant.mrp =request.POST.get("mrp")
        variant.selling_price=request.POST.get("selling_price")
        variant.cost_price=request.POST.get("cost_price")
        variant.stock_quantity=request.POST.get("stock_quantity")
        variant.weight=request.POST.get("weight")
        variant.length= request.POST.get("length")
        variant.width=request.POST.get("width")
        variant.height=request.POST.get("height")
        variant.tax_percentage=request.POST.get("tax_percentage")
        variant.save()

        return redirect("/sellerhome/")
    return render(request,"seller/sellerproductupdate.html",{"sub": sub,"product": product,"variant": variant})    

@seller_required
def toggleproductstatus(request, slug):
    seller=SellerProfile.objects.get(user=request.user)
    product = Product.objects.get(slug=slug, seller=seller)

    if product.is_active:
        product.is_active = False
    else:
        product.is_active = True
    product.save()
    return redirect("/sellerhome/")


@seller_required
def sellerinactive(request):
    seller=SellerProfile.objects.get(user=request.user)
    products=(Product.objects.filter(seller=seller,is_active=False).prefetch_related("variants__images").order_by("-created_at"))
    return render(request, "seller/inactiveproductdetails.html", {"products": products,"seller":seller})


@seller_required
def sellerimage(request,id):
    product=Product.objects.get(id=id)
    images=ProductImage.objects.filter(variant=ProductVariant.objects.get(product=product))
    data=ProductImage()
    if request.method=="POST":
        data.variant=ProductVariant.objects.get(product=product)
        data.images=request.FILES.get("images")
        data.alt_text=request.POST.get("alt_text")
        data.is_primary = bool(request.POST.get("is_primary"))
        data.save()
    return render(request,"seller/sellerproductimages.html",{"images":images})


@seller_required
def imagedelete(request,id):
    data=ProductImage.objects.get(id=id)
    data.delete()
    return redirect("/sellerimage/")

@seller_required
def selleratribute(request):
    atr=AttributeOption()
    AT=Attribute.objects.all()
    if request.method=="POST":
        atr.attribute=Attribute.objects.get(id=request.POST.get('Atribute'))
        atr.value=request.POST.get('value')
        atr.save()
        return redirect('/sellerhome/')

    return render(request,"seller/sellerattribute.html",{"AT":AT})


# @seller_required
# def sellerupdateatribute(request):
#     atr=AttributeOption()
#     AT=Attribute.objects.all()

#     if request.method=="POST":
#         atr.attribute=Attribute.objects.get(id=request.POST.get('Atribute'))
#         atr.value=request.POST.get('value')
#         atr.save()
#         return redirect('/sellerhome/')

#     return render(request,"seller/sellerattribute.html",{"AT":AT})

@seller_required
def productsingle(request,slug):
    product=Product.objects.get(slug=slug)
    data=ProductVariant.objects.get(product=product)
    images=ProductImage.objects.filter(variant=data)
    return render(request,"seller/productsingleview.html",{"data":data,"product":product,"images":images})

@seller_required
def sellerorder(request):
    seller = SellerProfile.objects.get(user=request.user)
    order=OrderItem.objects.filter(seller=seller)
    
    active_orders=0
    shipments_out=0
    revenue=0

    for item in order:
        if item.order.order_status=="placed":
            active_orders += 1
        if item.order.order_status=="shipped":
            shipments_out += 1
        revenue += item.order.total_amount
    return render(request,"seller/sellerordermanagement.html",{"order":order,"active_orders":active_orders,"shipments_out":shipments_out,"revenue":revenue,"seller":seller})

@seller_required
def productdelete(request,id):
    product=Product.objects.get(id=id)
    product.delete()
    return redirect("/sellerhome/")




@seller_required
def sellerreturns(request):
    seller = SellerProfile.objects.get(user=request.user)
    returns = ReturnRequest.objects.filter(seller=seller).order_by("-created_at")
    return render(request,"seller/sellerreturn.html",{"returns": returns,"seller":seller})





@seller_required
def sellerdashboard(request):

    seller = SellerProfile.objects.get(user=request.user)

    order_items = OrderItem.objects.filter(seller=seller)
    return_requests = ReturnRequest.objects.filter(seller=seller)
    products=Product.objects.filter(is_active=True)

    total_revenue = 0
    total_products = 0
    total_returns = 0
    active_orders=0
    activelisting=len(products)

    for item in order_items:
        total_revenue += item.price_at_purchase * item.quantity
        total_products += item.quantity

    for r in return_requests:
        total_returns += 1

    for item in order_items:
        if item.order.order_status=="placed":
            active_orders += 1    

    return render(request, "seller/sellerdashboard.html",{"total_revenue":total_revenue,"total_products":total_products,"total_returns":total_returns,"active_orders":active_orders,"activelisting":activelisting,"seller":seller})