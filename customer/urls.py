from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.products, name='products'),
    path('search/', views.search_products, name='search'),
    path('category/<slug:category_slug>', views.category_view, name='category_view'),
    path('category/<slug:category_slug>/subcategory/<slug:subcategory_slug>', views.subcategory_products, name='subcategory_products'),
    path('register/', views.user_register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.user_profile, name='profile'),
    path("verify-email/", views.verify_email, name="verify_email"),
    # path('update_profile_image/', views.user_profile_image_update, name='update_profile_image'),
    # path('update_profile/', views.user_profile_update, name='update_profile'),

    path('addresses/', views.user_addresses, name='user_addresses'),
    path('add_addresses/', views.user_address_adding, name='add_address'),
    path('address_update/<uuid:address_id>/', views.user_address_update, name='update_address'),
    path('address_delete/<uuid:address_id>/', views.user_address_delete, name='delete_address'),

    path('cart/', views.user_cart, name='cart'),
    path('cart/add/<slug:slug>', views.user_addto_cart, name='add_cart'),
    path('cart/update/<uuid:item_id>/<str:action>/', views.cart_update_quantity, name='cart_update_quantity'),
    path('cart/remove/<uuid:item_id>/', views.cart_remove_item, name='cart_remove_item'),

    path('cart/checkout/', views.user_checkout, name='cart_checkout'),

    path('wishlist/', views.user_wishlist, name='wishlist'),
    # path('wishlist/add/<uuid:variant_id>/', views.add_to_wishlist_default, name='wishlist_add'),
    path('cart/add/<slug:slug>/', views.user_addto_cart, name='user_addto_cart'),
    # path('wishlist/remove/<uuid:item_id>/', views.remove_wishlist_item, name='remove_wishlist_item'),
    path('wishlist/remove/<str:item_id>/', views.remove_wishlist_item, name='remove_wishlist_item'),
    # path('wishlist/toggle/<uuid:variant_id>/', views.toggle_wishlist_item, name='wishlist_toggle'),

    path('wishlist/toggle/<slug:variant_slug>/', views.toggle_wishlist_item, name='wishlist_toggle'),
    path('wishlist/set-active/', views.set_active_wishlist, name='set_active_wishlist'),
    path('wishlist/delete/<uuid:wishlist_id>/', views.delete_wishlist, name='delete_wishlist'),
    path('wishlist/create/', views.create_wishlist, name='create_wishlist'),
    path('wishlist/rename/<uuid:wishlist_id>/', views.rename_wishlist, name='rename_wishlist'),

    path('orders/', views.user_orders, name='orders'),
    path('track-order/<uuid:order_id>/', views.user_track, name='track_order'),
    path('checkout/', views.user_checkout, name='checkout'),

    path('buy-now/<slug:slug>/', views.buy_now_checkout, name='buy_now_checkout'),

    path('checkout/process/', views.user_checkout_process, name='checkout_process'),
    path('order/success/<uuid:order_id>/', views.order_success, name='order_success'),
    path('order/<uuid:order_id>/', views.order_detail, name='order_detail'),
    path('review/submit/', views.submit_review, name='submit_review'),
    path('my-reviews/', views.my_reviews, name='my_reviews'),
    path('review/edit/<uuid:review_id>/', views.edit_review, name='edit_review'),
]
