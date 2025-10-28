from django.urls import path
from . import views

urlpatterns = [
    path('', views.highlight_list, name='highlight_list'),
    path('add/', views.add_book_page, name='add_book_page'),  # new dedicated page
    path('add-action/', views.add_highlight, name='add_highlight'),  # existing POST handler
    path('delete/<int:pk>/', views.delete_highlight, name='delete_highlight'),
    path('reorder/', views.reorder_highlight, name='reorder_highlight'),
    path('news/add/', views.add_news, name='add_news'),
    path('news/delete/<int:pk>/', views.delete_news, name='delete_news'),

]
