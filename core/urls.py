from django.urls import path
from . import views

urlpatterns = [
    path('buy-again/<uuid:order_id>/<uuid:item_id>/', views.buy_again, name='buy_again'),
    path('helpe-center/', views.helpe_center, name='helpe_center'),
    path('support-or-contact/', views.support_or_contact, name='support_or_contact'),
    path('about/', views.about, name='about'),
    path('shipping-info/', views.shipping_info, name='shipping_info'),
    path('privacypolicy/', views.privacypolicy, name='privacypolicy'),
    # path('login/', views.login_view, name='login'),
    # path('home/', views.main_home, name='main_home'),
    # path('order-details/', views.order_details, name='order_details'),  # Moved to customer app

    path('product/<slug:slug>', views.product_single, name='product_single'),
]
