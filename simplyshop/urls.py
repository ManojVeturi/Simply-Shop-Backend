from django.urls import path
from .views import (
    RegisterView,
    login_view,
    google_login,
    get_cart,
    add_to_cart,
    update_cart_item
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', login_view, name='login'),
    path('auth/google-login/', google_login, name='google-login'),
    path('cart/', get_cart, name='cart'),
    path('cart/add/', add_to_cart, name='cart-add'),
    path('cart/<int:pk>/', update_cart_item, name='cart-update-delete'),
]
