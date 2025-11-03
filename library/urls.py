from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('',login_required(views.library_home, login_url='login'), name='library'),
    path('remove/<int:book_id>/',login_required(views.remove_from_collection, login_url='login'), name='remove_from_collection'),
]
