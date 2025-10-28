from django.db import models
from authentication.models import User
from author.models import Book, Chapter  # assuming your main book app is called 'books'

class Library(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='library')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Library"


class History(models.Model):
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='history')
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    last_read_chapter = models.ForeignKey(Chapter, null=True, blank=True, on_delete=models.SET_NULL)
    last_read_time = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_read_time']

    def __str__(self):
        return f"{self.book.bname} ({self.library.user.username})"


class Collection(models.Model):
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='collection')
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    last_read_chapter = models.ForeignKey(Chapter, null=True, blank=True, on_delete=models.SET_NULL)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('library', 'book')
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.book.bname} in {self.library.user.username}'s Collection"
