from django.urls import path
from . import views

urlpatterns = [
    path('buy-again/', views.buy_again, name='buy_again'),
    # path('login/', views.login_view, name='login'),
    # path('home/', views.main_home, name='main_home'),
    path('order-details/', views.order_details, name='order_details'),
    path('product/<slug:slug>', views.product_single, name='product_single'),
]
