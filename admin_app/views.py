from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login ,logout
from django.contrib import messages
from core.models import User
from django.db.models import Sum , Count ,Avg
from seller.models import SellerProfile, Product, ProductVariant ,SubCategory
from customer.models import OrderItem 
from django.db.models import Prefetch
from django.db.models import Q, Min, Sum 
from core.models import Category, SubCategory, Banner



# Create your views here.
def adminlogin(request):
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
            if data.role == "ADMIN":
                login(request, data)
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect("/adminhome/")
            else:
                error_msg = "Invalid username/email or password"
        else:
            error_msg = "Invalid username/email or password"

    return render(request, "admin-templates/adminlogin.html", {'error_message': error_msg, 'saved_username': saved_username})




def adminhome(request):
    total_sellers = SellerProfile.objects.filter(status="APPROVED").count()

    seller_requests = SellerProfile.objects.filter(
        status="PENDING"
    ).count()

    live_products = Product.objects.filter(
        is_active=True,
        approval_status='APPROVED'
    ).count()

    revenue = OrderItem.objects.filter(
    order__order_status='delivered'  
).aggregate(total=Sum('price_at_purchase'))['total'] or 0

    context = {
        "total_sellers": total_sellers,
        "seller_requests": seller_requests,
        "live_products": live_products,
        "revenue": revenue,
    }

    return render(request, "admin-templates/adminhome.html", context)





def adminsellerapproval(request):
    sellers = SellerProfile.objects.filter(status='PENDING').select_related('user')
    return render(request,"admin-templates/adminsellerapproaval.html",{
        "sellers": sellers
    })




def approve_seller(request, id):
    if request.method == "POST":
        seller = SellerProfile.objects.filter(id=id).first()

        if seller:
            seller.status = 'APPROVED'
            seller.save()

    return redirect("/adminsellerapproval/")





def reject_seller(request, id):
    if request.method == "POST":
        seller = SellerProfile.objects.filter(id=id).first()

        if seller:
            seller.status = 'REJECTED'
            seller.save()

    return redirect('/adminsellerapproval/')




def product(request):
    products = Product.objects.filter(
        approval_status='PENDING'
    ).select_related(
        'seller', 'subcategory__category'
    ).prefetch_related(
        'variants__images'
    )
    return render(request,"admin-templates/adminproduct.html",{"products": products})




def approve_product(request, id):
    if request.method == "POST":
        product = Product.objects.get(id=id)
        if product:
            product.approval_status = 'APPROVED'
            product.save()
    return redirect('/adminproduct/')





def reject_product(request, id):
    if request.method == "POST":
        product = Product.objects.get(id=id)
        if product:
            product.approval_status = 'REJECTED'
            product.save()
    return redirect('/adminproduct/')




def approved_products(request):
    search = request.GET.get("search")
    subcategory = request.GET.get("subcategory")

    products = Product.objects.filter(
        approval_status="APPROVED",
        is_active=True
).annotate(
    total_stock=Sum("variants__stock_quantity")
).select_related("subcategory", "seller").prefetch_related("variants")

   
    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(brand__icontains=search) |
            Q(variants__sku_code__icontains=search)
        ).distinct()

    if subcategory:
        products = products.filter(subcategory_id=subcategory)

    subcategories = SubCategory.objects.all()

    context = {
        "products": products,
        "subcategories": subcategories,
        "selected_subcategory": subcategory,
        "search_query": search,
    }

    return render(request, "admin-templates/approvedproducts.html", context)




def approved_sellers(request):
    search = request.GET.get("search")
    sellers = SellerProfile.objects.filter(status="APPROVED").select_related("user")
    if search:
        sellers = sellers.filter(
            Q(store_name__icontains=search) |
            Q(user__username__icontains=search) |
            Q(user__email__icontains=search)
        )
    sellers = sellers.annotate(
        total_products=Count("products")
    )
    total_sellers = sellers.count()
    avg_rating = sellers.aggregate(avg=Avg("rating"))["avg"] or 0
    banned_count = SellerProfile.objects.filter(status="REJECTED").count()
    context = {
        "sellers": sellers,
        "total_sellers": total_sellers,
        "avg_rating": round(avg_rating, 1),
        "banned_count": banned_count,
        "search_query": search,
    }
    return render(request, "admin-templates/adminseller.html", context)

   

  

def rejected_sellers(request):
    search = request.GET.get("search")

    sellers = SellerProfile.objects.filter(status="REJECTED").select_related("user")
    if search:
        sellers = sellers.filter(
            Q(store_name__icontains=search) |
            Q(user__username__icontains=search) |
            Q(user__email__icontains=search)
        )

    context = {
        "sellers": sellers,
        "search": search,
    }

    return render(request, "admin-templates/rejectedsellers.html", context)

def reapprove_seller(request,id):
    seller = SellerProfile.objects.get(id=id)

    if seller:
        seller.status = 'APPROVED'
        seller.save()
        messages.success(request, "Seller re-approved successfully")
    else:
        messages.error(request, "Seller not found")

    return redirect('/rejectedsellers/')



def rejected_products(request):
    search = request.GET.get("search")
    subcategory = request.GET.get("subcategory")

    products = Product.objects.filter(
        approval_status="REJECTED"
    ).select_related("subcategory", "seller").prefetch_related("variants")

   
    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(brand__icontains=search) |
            Q(variants__sku_code__icontains=search)
        ).distinct()

    
    if subcategory:
        products = products.filter(subcategory_id=subcategory)

    context = {
        "products": products,
        "subcategories": SubCategory.objects.all(),
        "search_query": search,
        "selected_subcategory": subcategory,
    }

    return render(request, "admin-templates/rejectedproducts.html", context)


def reapprove_product(request, id):
    updated = Product.objects.get(id=id)

    if updated:
        updated.approval_status = 'APPROVED'
        updated.save()
        messages.success(request, "Product re-approved successfully")
    else:
        messages.error(request, "Product not found")

    return redirect("/rejectedproducts/")


def rejectseller(request, id):
    if request.method == "POST":
        seller = SellerProfile.objects.filter(id=id).first()

        if seller:
            seller.status = 'REJECTED'
            seller.save()

    return redirect('/approvedsellers/')

def category_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        image = request.FILES.get("image")
        description = request.POST.get("description")
        if name:
            Category.objects.create(
                name=name,
                image=image,
                description=description
            )
        return redirect('/category/')
    categories = Category.objects.all().order_by('-created_at')
    return render(request, 'admin-templates/category.html', {'categories': categories})

def toggle_category_status(request, id):
    category = Category.objects.get(id=id)

    if category:
        category.is_active = not category.is_active
        category.save()
    return redirect('/category/')

def delete_category(request, id):
    category = Category.objects.get(id=id)
    if category:
        category.delete()
    return redirect('/category/')

def subcategory_management(request):
    categories = Category.objects.all()
    subcategories = SubCategory.objects.select_related('category').all().order_by('-created_at')

    if request.method == "POST":
        category_id = request.POST.get("category")
        name = request.POST.get("name")
        image = request.FILES.get("image")

        if category_id and name:
            category = Category.objects.get(id=category_id)

            SubCategory.objects.create(
                category=category,
                name=name,
                image=image
            )

        return redirect('subcategory_management')  # use your URL name

    context = {
        "categories": categories,
        "subcategories": subcategories
    }
    return render(request, "admin-templates/subcategory.html", context)

def delete_subcategory(request, id):
    sub = SubCategory.objects.get(id=id)
    sub.delete()
    return redirect('subcategory_management')

def banner_management(request):
    if request.method == "POST":
        title = request.POST.get("title")
        image_url = request.POST.get("image_url")
        redirect_url = request.POST.get("redirect_url")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")

        if title and image_url and start_date and end_date:
            Banner.objects.create(
                title=title,
                image_url=image_url,
                redirect_url=redirect_url,
                start_date=start_date,
                end_date=end_date
            )
        return redirect('banner_management')

    banners = Banner.objects.all().order_by('-start_date')
    return render(request, 'admin-templates/banner.html', {'banners': banners})

def delete_banner(request, id):
    Banner.objects.filter(id=id).delete()
    return redirect('banner_management')