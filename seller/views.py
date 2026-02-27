from django.shortcuts import render,redirect
from django.http import HttpResponse
from core.models import User,Category,SubCategory
from .models import SellerProfile,Product,ProductVariant,ProductImage,Attribute,AttributeOption,VariantAttributeBridge
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
                                          role="seller",
                                          profile_image=request.FILES.get("profile_image"),
                                          )
            user.save()
            sellr=SellerProfile.objects.create( user=user,
                                                store_name=request.POST.get("store_name"),
                                                store_slug=slugify(request.POST.get("store_name")),
                                                gst_number=request.POST.get("gst_number"),
                                                pan_number=request.POST.get("pan_number"),
                                                bank_account_number=request.POST.get("bank_account_number"),
                                                ifsc_code=request.POST.get("ifsc_code"),
                                                business_address=request.POST.get("business_address"),
                                                )
            sellr.save()
            return redirect("/login/")
    return render(request,"seller/sellerregistration.html")

def sellerlogin(request):
    if request.method=="POST":
        username=request.POST.get("username")
        password=request.POST.get("password")
        data=authenticate(request,username=username,password=password)
        if data:
            if data.role =="seller":
                login(request,data)
                return redirect("/sellerhome/")
                
            else:
                messages.error(request,"you are not allowed")
        else:
            return redirect("/regis/")    
    return render(request,"seller/sellerlogin.html")


@seller_required
def sellerhome(request):
    seller=SellerProfile.objects.get(user=request.user)
    products=(Product.objects.filter(seller=seller).prefetch_related("variants__images").order_by("-created_at"))
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
        data=Product()
        datas=ProductVariant()
        data.seller=SellerProfile.objects.get(user=request.user)
        m=SubCategory.objects.get(id=request.POST.get("subcategory"))
        data.subcategory=m
        data.name=request.POST.get("name")
        data.slug=request.POST.get("slug")
        data.description=request.POST.get("description")
        data.brand=request.POST.get("brand")
        data.model_number=request.POST.get("model_number")
        data.return_days=request.POST.get("return_days")
        data.approval_status=request.POST.get("approval_status")
        data.is_cancellable=request.POST.get("is_cancellable") is not None
        data.is_returnable=request.POST.get("is_returnable") is not None
        data.save()
        datas.product=data
        datas.sku_code=request.POST.get("sku_code")
        datas.mrp=request.POST.get("mrp")
        datas.selling_price=request.POST.get("selling_price")
        datas.cost_price=request.POST.get("cost_price")
        datas.stock_quantity=request.POST.get("stock_quantity")
        datas.weight=request.POST.get("weight")
        datas.length=request.POST.get("length")
        datas.width=request.POST.get("width")
        datas.height=request.POST.get("height")
        datas.tax_percentage=request.POST.get("tax_percentage")

        datas.save()

        return redirect("/sellerhome/")

    return render(request,"seller/sellerproduct.html",{"sub":sub})    

@seller_required
def sellerproduct_update(request, id):
    sub = SubCategory.objects.all()
    product = Product.objects.get(id=id)
    variant = ProductVariant.objects.get(product=product)
    if request.method == "POST":
        product.seller = SellerProfile.objects.get(user=request.user)
        m = SubCategory.objects.get(id=request.POST.get("subcategory"))
        product.subcategory = m
        product.name = request.POST.get("name")
        product.slug = request.POST.get("slug")
        product.description = request.POST.get("description")
        product.brand = request.POST.get("brand")
        product.model_number = request.POST.get("model_number")
        product.return_days = request.POST.get("return_days")
        product.approval_status = request.POST.get("approval_status")
        product.is_cancellable = request.POST.get("is_cancellable") is not None
        product.is_returnable = request.POST.get("is_returnable") is not None
        product.save()
        variant.product = product
        variant.sku_code = request.POST.get("sku_code")
        variant.mrp = request.POST.get("mrp")
        variant.selling_price = request.POST.get("selling_price")
        variant.cost_price = request.POST.get("cost_price")
        variant.stock_quantity = request.POST.get("stock_quantity")
        variant.weight = request.POST.get("weight")
        variant.length = request.POST.get("length")
        variant.width = request.POST.get("width")
        variant.height = request.POST.get("height")
        variant.tax_percentage = request.POST.get("tax_percentage")
        variant.save()

        return redirect("/sellerhome/")
    return render(request,"seller/sellerproductupdate.html",{"sub": sub,"product": product,"variant": variant})    


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
    return render(request,"seller/sellerordermanagement.html")


   