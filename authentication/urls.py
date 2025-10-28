
from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path("signup/", views.signup_view, name="signup"),
    path('logout/', views.logout_view, name='logout'),
    path('update/profile',login_required(views.update_profile, login_url='login'), name='updateprofile'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('send-otp/', views.send_otp, name='send_otp'),
    path('verify-email-otp/', views.verify_email_otp, name='verify_email_otp'),
    path('forgot-password/', views.forgotpassword, name='forgotpassword'),
]