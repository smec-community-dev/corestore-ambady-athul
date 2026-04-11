from django.urls import path
from .import views

urlpatterns = [
     path("adlogin/",views.adminlogin),
    path("adminhome/",views.adminhome),
    path("adminsellerapproval/",views.adminsellerapproval),
    path("adminsellersapprove/<int:id>/", views.approve_seller, name="approve_seller"),
    path("adminsellersreject/<int:id>/", views.reject_seller, name="reject_seller"),
    path("adminproduct/",views.product),
    path("productsapprove/<int:id>/", views.approve_product, name="approve_product"),
    path("productsreject/<int:id>/", views.reject_product, name="reject_product"),
    path("approvedproducts/", views.approved_products, name="approved_products"),
    path("approvedsellers/", views.approved_sellers),
    path("rejectedsellers/", views.rejected_sellers ),
    path("reapproveseller/<int:id>/", views.reapprove_seller, name="reapprove_seller"),
    path("rejectedproducts/", views.rejected_products, name="rejected_products"),
    path("reapproveproduct/<int:id>/", views.reapprove_product, name="reapprove_product"),
    path("admisellersreject/<int:id>/", views.rejectseller, name="rejectseller"),
    path('category/', views.category_view,),
    path('toggle/<uuid:id>/', views.toggle_category_status, name='toggle_category'),
    path('categorydelete/<uuid:id>/', views.delete_category, name='delete_category'),
    path('subcategories/', views.subcategory_management, name='subcategory_management'),
    # path('subcategoriestoggle/<uuid:id>/', views.toggle_subcategory_status, name='toggle_subcategory'),
    path('subcategoriesdelete/<uuid:id>/', views.delete_subcategory, name='delete_subcategory'),
    # path('subcategoriesedit/<uuid:id>/', views.edit_subcategory, name='edit_subcategory'),
    path('banners/', views.banner_management, name='banner_management'),
    path('bannerdelete/<uuid:id>/', views.delete_banner, name='delete_banner'),

]