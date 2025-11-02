from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Q, F, Sum
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from django.db import transaction
from library.models import Library, Collection, History
from author.models import Book, Chapter, Comment, Review
from moderator.models import HighlightedBook, News

# Create your views here.

def home(request):
    top_books = HighlightedBook.objects.filter(category='TOP').select_related('book').order_by('order')[:15]
    featured_books = HighlightedBook.objects.filter(category='FEATURED').select_related('book').order_by('order')[:15]
    books = Book.objects.all()
    news_items = News.objects.all().order_by('-added_on')[:10]  # latest 10 news items

    return render(request, 'reader/rhome.html', {
        'books': books,
        'top_books': top_books,
        'featured_books': featured_books,
        'news_items': news_items,
    })

def browse(request):
    query = request.GET.get('q', '')  # Get search keyword
    books_list = Book.objects.all()

    if query:
        books_list = books_list.filter(
            Q(bname__icontains=query) |
            Q(user__username__icontains=query) |
            Q(genre__icontains=query)
        )

    books_list = books_list.order_by('bname')  # Sort A–Z

    paginator = Paginator(books_list, 20)
    page_number = request.GET.get('page')
    books = paginator.get_page(page_number)

    return render(request, 'reader/rbrowse.html', {'books': books, 'query': query})


def ranking(request):
    return render(request, 'reader/rranking.html')

def contest(request):
    return render(request, 'reader/rcontest.html')

def about(request):
    return render(request, 'reader/rabout.html')

def book(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    chapters = book.chapters.order_by('order')
    top_books = HighlightedBook.objects.filter(category='TOP').select_related('book').order_by('order')[:15]

    book.views = models.F('views') + 1
    book.save(update_fields=["views"])
    book.refresh_from_db()  # refresh actual value

    chapters = book.chapters.order_by('order')

    total_likes = chapters.aggregate(Sum('likes'))['likes__sum'] or 0

    history = None
    collection_books = []

    if request.user.is_authenticated:
        library = getattr(request.user, 'library', None)

        if library:
            # Filter by library instead of user
            history = History.objects.filter(library=library, book=book).first()
            collection_books = list(library.collection.values_list('book_id', flat=True))

    return render(request, 'reader/rbook.html', {
        'book': book,
        'chapters': chapters,
        'collection_books': collection_books,
        'total_likes': total_likes, 
        "rating_range": range(1, 6),
        'history': history,  
        'top_books': top_books,
    })



def read(request, book_id, chapter_id):
    book = get_object_or_404(Book, id=book_id)
    chapter = get_object_or_404(Chapter, id=chapter_id, Book=book)  
    prev_chapter = Chapter.objects.filter(Book=book, order__lt=chapter.order).order_by('-order').first()
    next_chapter = Chapter.objects.filter(Book=book, order__gt=chapter.order).order_by('order').first()
   

    # -----------------------------
    # Update Library History
    # -----------------------------
    library, _ = Library.objects.get_or_create(user=request.user)

    # Remove existing entry for this book to move it to the top
    History.objects.filter(library=library, book=book).delete()

    # Enforce max 15 books
    if History.objects.filter(library=library).count() >= 15:
        oldest = History.objects.filter(library=library).order_by('last_read_time').first()
        if oldest:
            oldest.delete()

    # Add new history entry
    History.objects.create(library=library, book=book, last_read_chapter=chapter)


    return render(request, "reader/rread.html", {
        "book": book,
        "chapter": chapter,
        "chapters": book.chapters.all().order_by("order"),
        "prev_chapter": prev_chapter,
        "next_chapter": next_chapter,
    })

@login_required
def add_to_collection(request, book_id):
    if not request.user.is_authenticated:
        return redirect('login')

    book = get_object_or_404(Book, id=book_id)
    library, _ = Library.objects.get_or_create(user=request.user)
    existing = Collection.objects.filter(library=library, book=book)

    if existing.exists():
        existing.delete()  # remove
    else:
        Collection.objects.create(library=library, book=book)
        # enforce 100-book limit
        collection_qs = Collection.objects.filter(library=library).order_by('-added_at')
        if collection_qs.count() > 100:
            for old_entry in collection_qs[100:]:
                old_entry.delete()

    return redirect('book', book_id=book.id)

@require_POST
@login_required
def increment_chapter_view(request, chapter_id):
    """
    Count a view after 10 seconds of reading.
    One view per user/session per chapter.
    """
    chapter = get_object_or_404(Chapter, id=chapter_id)
    book = chapter.Book

    # --- session handling ---
    viewed_chapters = request.session.get("viewed_chapters", [])
    viewed_chapters = [str(cid) for cid in viewed_chapters]  # normalize

    # --- already counted? ---
    if str(chapter_id) in viewed_chapters:
        return JsonResponse({
            "success": False,
            "message": "Already counted",
            "chapter_views": chapter.views,
            "book_views": book.views,
        })

    # --- atomic increment ---
    Chapter.objects.filter(id=chapter_id).update(views=F("views") + 1)
    chapter.Book.__class__.objects.filter(id=book.id).update(views=F("views") + 1)

    # refresh values
    chapter.refresh_from_db(fields=["views"])
    book.refresh_from_db(fields=["views"])

    # --- update session (persist immediately) ---
    viewed_chapters.append(str(chapter_id))
    request.session["viewed_chapters"] = viewed_chapters
    request.session.modified = True
    request.session.save()  # <— ensure it's written now, not later

    return JsonResponse({
        "success": True,
        "message": "View counted",
        "chapter_views": chapter.views,
        "book_views": book.views,
    })


# views.py
@csrf_exempt
def toggle_like(request, book_id):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Login required"}, status=403)

    try:
        book = Book.objects.get(id=book_id)

        if request.user in book.favorites.all():
            # Unlike
            book.favorites.remove(request.user)
            book.likes = models.F('likes') - 1
            liked = False
        else:
            # Like
            book.favorites.add(request.user)
            book.likes = models.F('likes') + 1
            liked = True

        book.save(update_fields=["likes"])
        book.refresh_from_db()  # Get the actual updated count

        return JsonResponse({"likes": book.likes, "liked": liked})

    except Book.DoesNotExist:
        return JsonResponse({"error": "Book not found"}, status=404)

@require_POST
@login_required
def toggle_chapter_like(request, chapter_id):
    chapter = get_object_or_404(Chapter, id=chapter_id)

    with transaction.atomic():
        liked = chapter.toggle_like(request.user)
        # Re-fetch to ensure accurate like count after concurrent updates
        chapter.refresh_from_db(fields=["likes"])

    return JsonResponse({
        "liked": liked,
        "likes": chapter.likes,
    })


@require_POST
@login_required
def add_comment(request, chapter_id):
    """Add a new comment to a chapter."""
    chapter = get_object_or_404(Chapter, id=chapter_id)
    content = request.POST.get("content", "").strip()

    if not content:
        return JsonResponse({"error": "Empty comment"}, status=400)

    comment = Comment.objects.create(
        chapter=chapter,
        user=request.user,
        content=content
    )

    # update comment counter
    Chapter.objects.filter(id=chapter.id).update(comments_count=F("comments_count") + 1)
    chapter.refresh_from_db(fields=["comments_count"])

    return JsonResponse({
        "success": True,
        "comment_id": comment.id,
        "content": comment.content,
        "user": request.user.username,
        "created_at": comment.created_at.strftime("%Y-%m-%d %H:%M"),
        "comments_count": chapter.comments_count,
    })


@require_POST
@login_required
def toggle_comment_like(request, comment_id):
    """Toggle like/unlike for a comment."""
    comment = get_object_or_404(Comment, id=comment_id)
    liked = comment.toggle_like(request.user)
    return JsonResponse({
        "liked": liked,
        "likes": comment.likes,
    })

# --- REVIEWS & RATINGS ---
@login_required
def add_or_edit_review(request, book_id):
    """Create or update a user's review for a specific book."""
    book = get_object_or_404(Book, id=book_id)

    if request.method == "POST":
        rating = request.POST.get("rating")
        review_text = request.POST.get("review", "").strip()

        # Validate rating
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError
        except (ValueError, TypeError):
            return JsonResponse({"error": "Invalid rating value"}, status=400)

        # Update or create review
        review, created = Review.objects.update_or_create(
            book=book,
            user=request.user,
            defaults={"rating": rating, "review": review_text},
        )

        # Update book rating stats
        book.update_average_rating()

        return JsonResponse({
            "success": True,
            "created": created,
            "rating": review.rating,
            "review": review.review,
            "avg_rating": book.rating,
            "total_ratings": book.total_ratings,
        })

    return JsonResponse({"error": "Invalid request method"}, status=400)


@login_required
def delete_review(request, book_id):
    """Delete the current user's review for a book."""
    book = get_object_or_404(Book, id=book_id)
    try:
        review = Review.objects.get(book=book, user=request.user)
        review.delete()
        book.update_average_rating()
        return JsonResponse({
            "success": True,
            "message": "Review deleted",
            "avg_rating": book.rating,
            "total_ratings": book.total_ratings,
        })
    except Review.DoesNotExist:
        return JsonResponse({"error": "No review found"}, status=404)


@login_required
def delete_review_by_id(request, review_id):
    """Delete a review by ID (used by book owner or admin)."""
    review = get_object_or_404(Review, id=review_id)
    book = review.book
    if request.user == review.user or request.user == book.user or request.user.is_staff:
        review.delete()
        book.update_average_rating()
        return JsonResponse({"success": True, "message": "Review deleted"})
    return JsonResponse({"error": "Permission denied"}, status=403)


@login_required
def check_review(request, book_id):
    """Check if the current user has already reviewed a book."""
    book = get_object_or_404(Book, id=book_id)
    try:
        review = Review.objects.get(book=book, user=request.user)
        return JsonResponse({
            "exists": True,
            "rating": review.rating,
            "review": review.review,
        })
    except Review.DoesNotExist:
        return JsonResponse({"exists": False})