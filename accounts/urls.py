from django.contrib import admin
from django.urls import path
from .views import UserRegistationView, UserLoginView, UserLogoutView,CustomLogoutView,UserBankAccountUpdateView,PasswordChangeView

urlpatterns = [
    path("register/", UserRegistationView.as_view(), name="register"),
    path("login/", UserLoginView.as_view(), name="login"),
    # path('logout/', UserLogoutView.as_view(), name='logout'),
    path("logout/", CustomLogoutView.as_view(), name="logout"),
    path('profile/', UserBankAccountUpdateView.as_view(), name='profile' ),
    path('password_change/', PasswordChangeView.as_view(), name='password_change')
]
