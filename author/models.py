from django.db import models
from authentication.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Book(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="books")

    BOOK_TYPES = [
        ('novel', 'Novel'),
        ('comic', 'Comic'),
        ('shortstory', 'Short Story'),
    ]

    AGE_RATINGS = [
        ('All Ages', 'All Ages'),
        ('13+', '13+'),
        ('16+', '16+'),
        ('18+', '18+'),
    ]

    bname = models.CharField("Book Name", max_length=100)
    btype = models.CharField("Type", choices=BOOK_TYPES, max_length=20)
    genre = models.CharField("Genre", max_length=50)
    agerating = models.CharField("Age Rating", choices=AGE_RATINGS, max_length=10)
    description = models.TextField("Description", max_length=1000)
    coverimage = models.ImageField(upload_to='book_covers/', default='book_covers/cover.png', null=True, blank=True)

    # --- STATS ---
    views = models.PositiveIntegerField(default=0)
    favorites = models.ManyToManyField(User, related_name="favorite_books", blank=True)
    rating = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    total_ratings = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.coverimage:
            self.coverimage = 'book_covers/cover.png'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.bname

    @property
    def avg_rating(self):
        return round(self.rating, 2)

    def increment_views(self):
        self.views += 1
        self.save(update_fields=["views"])

    def update_average_rating(self):
        """Recalculate and update the book's average rating."""
        reviews = self.reviews.all()
        if reviews.exists():
            avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
            self.rating = round(avg_rating, 2)
            self.total_ratings = reviews.count()
        else:
            self.rating = 0
            self.total_ratings = 0
        self.save(update_fields=['rating', 'total_ratings'])
    

class Chapter(models.Model):
    Book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="chapters")
    title = models.CharField(max_length=100)
    content = models.TextField()
    order = models.PositiveIntegerField()
    views = models.PositiveIntegerField(default=0)
    likes = models.PositiveIntegerField(default=0)
    liked_by = models.ManyToManyField(User, related_name="liked_chapters", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    comments_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.order}. {self.title}"

    def increment_views(self):
        self.views += 1
        self.save(update_fields=["views"])

    def toggle_like(self, user):
        """Add or remove a like from a user."""
        if user in self.liked_by.all():
            self.liked_by.remove(user)
            self.likes = models.F('likes') - 1
            liked = False
        else:
            self.liked_by.add(user)
            self.likes = models.F('likes') + 1
            liked = True
        self.save(update_fields=["likes"])
        self.refresh_from_db(fields=["likes"])
        return liked


class Comment(models.Model):
    chapter = models.ForeignKey(Chapter, related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    # --- Likes for comments ---
    likes = models.PositiveIntegerField(default=0)
    liked_by = models.ManyToManyField(User, related_name="liked_comments", blank=True)

    def __str__(self):
        return f"Comment by {self.user} on {self.chapter}"

    def toggle_like(self, user):
        """Add or remove a like from a user."""
        if user in self.liked_by.all():
            self.liked_by.remove(user)
            self.likes = models.F('likes') - 1
            liked = False
        else:
            self.liked_by.add(user)
            self.likes = models.F('likes') + 1
            liked = True
        self.save(update_fields=["likes"])
        self.refresh_from_db(fields=["likes"])
        return liked


class Review(models.Model):
    book = models.ForeignKey(Book, related_name="reviews", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review = models.TextField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('book', 'user')  # Each user can review once
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} rated {self.book.bname} ({self.rating}/5)"

    def save(self, *args, **kwargs):
        """Override save to update book rating stats automatically."""
        super().save(*args, **kwargs)
        self.update_book_rating()

    def delete(self, *args, **kwargs):
        """Recalculate average when review is deleted."""
        book = self.book
        super().delete(*args, **kwargs)
        book.update_average_rating()

    def update_book_rating(self):
        """Recalculate the average rating for the book."""
        reviews = Review.objects.filter(book=self.book)
        avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg'] or 0
        total_ratings = reviews.count()

        self.book.rating = round(avg_rating, 2)
        self.book.total_ratings = total_ratings
        self.book.save(update_fields=['rating', 'total_ratings'])
