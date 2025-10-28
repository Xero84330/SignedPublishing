from django.db import models
from authentication.models import User
from author.models import Book

class HighlightedBook(models.Model):
    CATEGORY_TOP = 'TOP'
    CATEGORY_FEATURED = 'FEATURED'
    CATEGORY_CHOICES = [
        (CATEGORY_TOP, 'Top Books'),
        (CATEGORY_FEATURED, 'Featured Books'),
    ]

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='highlighted_entries')
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    order = models.PositiveIntegerField(default=0)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    added_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'order']

    def __str__(self):
        return f"{self.book.bname} ({self.get_category_display()})"

class News(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to='news_images/', null=True, blank=True)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    added_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-added_on']

    def __str__(self):
        return self.title