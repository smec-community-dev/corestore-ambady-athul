from django.urls import path
from . import views
urlpatterns =[
    path("slogin/",views.sellerlogin),
    path("regis/",views.selleregis),
    path("sellerhome/",views.sellerhome),
    path("sellerprofile/",views.sellerprofile),
    path("slogout/",views.seller_logout),
    path("sellerproduct/",views.sellerproduct),
    path("sellerproductupdate/<int:id>/", views.sellerproduct_update),
    path("sellerimage/<int:id>/",views.sellerimage),
    path("imagedelete/<int:id>/",views.imagedelete),
    path("selleratribute/",views.selleratribute),
    path("sellerproductview/<str:slug>",views.productsingle),
    path("sellerorder/",views.sellerorder),
    path("togglestatus/<str:slug>",views.toggleproductstatus),
    path("sellerinactive/",views.sellerinactive),
    path("sellerreturn/",views.sellerreturns),
    path("sellerdashboard/",views.sellerdashboard),
    path("reviews/",views.seller_reviews),
    path('update-order-status/', views.update_order_status, name='update_order_status'),


]
