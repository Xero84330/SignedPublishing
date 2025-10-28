from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('', views.home, name='home'),
    path('home/browse/', views.browse, name='browse'),
    path('home/ranking/', views.ranking, name='ranking'),
    path('home/contest/', views.contest, name='contest'),
    path('home/about/', views.about, name='about'),
    path('home/book/<int:book_id>/', views.book, name='book'),
    path('home/read/<int:book_id>/<int:chapter_id>/', login_required(views.read, login_url='login'), name='read'),

    # --- Collections & Views ---
    path('book/<int:book_id>/add-to-collection/', views.add_to_collection, name='add_to_collection'),
    path('chapter/<int:chapter_id>/view/', views.increment_chapter_view, name='increment_chapter_view'),

    # --- Likes & Comments ---
    path('toggle-like/<int:book_id>/', views.toggle_like, name='toggle_like'),
    path('chapter/<int:chapter_id>/toggle-like/', views.toggle_chapter_like, name='toggle_chapter_like'),
    path('chapter/<int:chapter_id>/add-comment/', views.add_comment, name='add_comment'),

    # --- Reviews & Ratings ---
    path('book/<int:book_id>/review/', views.add_or_edit_review, name='add_or_edit_review'),
    path('book/<int:book_id>/review/delete/', views.delete_review, name='delete_review'),
    path('review/<int:review_id>/delete/', views.delete_review_by_id, name='delete_review_by_id'),  
    path('book/<int:book_id>/review/check/', views.check_review, name='check_review'),
]
