from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    path('product/<int:id>/', views.product_detail, name='product_detail'),

    path('product/add/', views.add_product, name='add_product'),

    path('product/update/<int:id>/', views.update_product, name='update_product'),

    path('product/delete/<int:id>/', views.delete_product, name='delete_product'),

    path('register/', views.register, name='register'),

    path('login/', views.user_login, name='login'),

    path('logout/', views.user_logout, name='logout'),

    path('cart/add/<int:id>/', views.add_to_cart, name='add_to_cart'),

    path('cart/', views.view_cart, name='view_cart'),

    path('cart/remove/<int:id>/', views.remove_cart, name='remove_cart'),

    path('checkout/', views.checkout, name='checkout'),

    path('orders/', views.my_orders, name='my_orders'),
]