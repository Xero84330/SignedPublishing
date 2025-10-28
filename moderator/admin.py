from django.contrib import admin
from .models import HighlightedBook, News

@admin.register(HighlightedBook)
class HighlightedBookAdmin(admin.ModelAdmin):
    list_display = ('book', 'category', 'order', 'added_by', 'added_on')
    list_filter = ('category',)
    search_fields = ('book__bname',)
    ordering = ('category', 'order')

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'added_by', 'added_on')
    search_fields = ('title', 'content')
    list_filter = ('added_on', 'added_by')
    ordering = ('-added_on',)