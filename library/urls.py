from django.urls import path
from . import views

urlpatterns = [
    path('', views.library_home, name='library'),
    path('remove/<int:book_id>/', views.remove_from_collection, name='remove_from_collection'),
]
