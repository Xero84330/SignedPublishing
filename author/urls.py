
from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('create/', login_required(views.create, login_url='login'), name='create'),
    path('create/payment', login_required(views.payment, login_url='login'), name='payment'),
    path('create/addbook', login_required(views.addbook, login_url='login'), name='addbook'),
    path('create/editbook/<int:book_id>/', login_required(views.editbook, login_url='login'), name='editbook'),
    path('create/addchapter/<int:book_id>/', login_required(views.addchapter, login_url='login'), name='addchapter'),
    path('create/abookpage/<int:book_id>/', login_required(views.abookpage, login_url='login'), name='abookpage'),
    path("create/<int:pk>/delete_chapter/", login_required(views.delete_chapter, login_url='login'), name="delete_chapter"),
    path('create/<int:chapter_id>/edit/', login_required(views.edit_chapter, login_url='login'), name='edit_chapter'),
    path("create/<int:pk>/delete_book/", login_required(views.delete_book, login_url='login'), name="delete_book"),
    path('create/statistics/<int:book_id>/', login_required(views.statistics, login_url='login'), name='statistics'),

]