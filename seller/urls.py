from django.urls import path
from . import views
urlpatterns =[
    path("login/",views.sellerlogin),
    path("regis/",views.selleregis),
    path("sellerhome/",views.sellerhome),
    path("sellerprofile/",views.sellerprofile),
    path("logout/",views.seller_logout),
    path("sellerproduct/",views.sellerproduct),
    path("sellerproductupdate/<int:id>/", views.sellerproduct_update),
    path("sellerimage/<int:id>/",views.sellerimage),
    path("imagedelete/<int:id>",views.imagedelete),
    path("selleratribute/",views.selleratribute),
    path("sellerproductview/<str:slug>",views.productsingle),
    path("sellerorder/",views.sellerorder),

]