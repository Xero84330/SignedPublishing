from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Max
from datetime import datetime
import calendar
from datetime import datetime, timedelta
from django.db.models import Sum
from django.shortcuts import render, get_object_or_404
from .models import Book, Chapter, Comment
from library.models import Collection
from django.utils import timezone
from moderator.models import News

def statistics(request, book_id):
    book = get_object_or_404(Book, id=book_id, user=request.user)
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)

    # Read range param from URL (?range=30)
    range_days = int(request.GET.get("range", 7))  # default 7
    
    # Basic stats
    today_views = Chapter.objects.filter(Book=book, created_at__date=today).aggregate(total=Sum("views"))["total"] or 0
    yesterday_views = Chapter.objects.filter(Book=book, created_at__date=yesterday).aggregate(total=Sum("views"))["total"] or 0

    today_likes = Chapter.objects.filter(Book=book, created_at__date=today).aggregate(total=Sum("likes"))["total"] or 0
    yesterday_likes = Chapter.objects.filter(Book=book, created_at__date=yesterday).aggregate(total=Sum("likes"))["total"] or 0

    today_comments = Comment.objects.filter(chapter__Book=book, created_at__date=today).count()
    yesterday_comments = Comment.objects.filter(chapter__Book=book, created_at__date=yesterday).count()

    today_bookmarks = Collection.objects.filter(book=book, added_at__date=today).count()

    def calc_growth(today, yesterday):
        if yesterday == 0:
            return 100 if today > 0 else 0
        return round(((today - yesterday) / yesterday) * 100, 1)

    view_growth = calc_growth(today_views, yesterday_views)
    like_growth = calc_growth(today_likes, yesterday_likes)
    comment_growth = calc_growth(today_comments, yesterday_comments)

    # Dynamic range stats
    daily_labels, daily_views, daily_likes, daily_comments, daily_bookmarks, daily_engagement = [], [], [], [], [], []

    for i in range(range_days):
        day = today - timedelta(days=(range_days - 1 - i))
        label = day.strftime("%b %d")

        views_sum = Chapter.objects.filter(Book=book, created_at__date=day).aggregate(Sum("views"))["views__sum"] or 0
        likes_sum = Chapter.objects.filter(Book=book, created_at__date=day).aggregate(Sum("likes"))["likes__sum"] or 0
        comments_sum = Comment.objects.filter(chapter__Book=book, created_at__date=day).count()
        bookmarks_sum = Collection.objects.filter(book=book, added_at__date=day).count()

        daily_labels.append(label)
        daily_views.append(views_sum)
        daily_likes.append(likes_sum)
        daily_comments.append(comments_sum)
        daily_bookmarks.append(bookmarks_sum)
        daily_engagement.append(views_sum + likes_sum + comments_sum + bookmarks_sum)

    engagement_data = {
        "views": today_views,
        "comments": today_comments,
        "bookmarks": today_bookmarks,
    }

    start_month = today.replace(day=1)
    next_month = (start_month + timedelta(days=32)).replace(day=1)

    update_dates = list(
        Chapter.objects.filter(
            Book=book,
            created_at__gte=start_month,
            created_at__lt=next_month
        ).values_list("created_at__day", flat=True)
    )

    context = {
        "book": book,
        "today_views": today_views,
        "today_likes": today_likes,
        "today_comments": today_comments,
        "view_growth": view_growth,
        "like_growth": like_growth,
        "comment_growth": comment_growth,
        "total_engagement": sum(engagement_data.values()),
        "top_chapters": book.chapters.order_by("-views", "-likes")[:5],
        "daily_labels": daily_labels,
        "today_bookmarks": today_bookmarks,
        "daily_views": daily_views,
        "daily_likes": daily_likes,
        "daily_comments": daily_comments,
        "daily_bookmarks": daily_bookmarks,
        "daily_engagement": daily_engagement,
        "engagement_data": engagement_data,
        "update_dates": update_dates,
        "range": range_days,  # send to template
    }

    return render(request, "author/astats.html", context)



def create(request):
    user_books = Book.objects.filter(user=request.user)
    news_items = News.objects.all().order_by('-added_on')[:10]
    return render(request, 'author/adashboard.html', 
                  {'books': user_books,
                   'news_items': news_items,
                   }
                  )

def payment(request):
    return render(request, 'author/apayment.html')

def abookpage(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    chapters = book.chapters.order_by('order')

    return render(request, 'author/abookpage.html', {
        'book': book,
        'chapters':chapters,
    })

def addbook(request):
    if request.method == 'POST':
        bname       = request.POST.get('bname')
        btype       = request.POST.get('btype')
        genre       = request.POST.get('genre')
        agerating   = request.POST.get('agerating')
        description = request.POST.get('description')
        coverimage  = request.FILES.get('coverimage')

        Book.objects.create(
            user=request.user,
            bname=bname,
            btype=btype,
            genre=genre,
            agerating=agerating,
            description=description,
            coverimage=coverimage
        )
        messages.success(request, f'Book "{bname}" created!')
        return redirect('create')

    # Show the list of books for the user (unchanged)
    user_books = Book.objects.filter(user=request.user)
    return render(request, 'author/addbook.html', {
        'books': user_books,
        'mode': 'add',          # <-- add this
    })


def editbook(request, book_id):
    book = get_object_or_404(Book, id=book_id, user=request.user)
    
    # CRITICAL FIX: Reload the image field so .url works
    book.refresh_from_db()

    if request.method == 'POST':
        book.btype       = request.POST.get('btype')
        book.genre       = request.POST.get('genre')
        book.agerating   = request.POST.get('agerating')
        book.description = request.POST.get('description')

        cover = request.FILES.get('coverimage')
        if cover:
            book.coverimage = cover

        book.save()
        messages.success(request, f'Book "{book.bname}" updated!')
        return redirect('create')

    user_books = Book.objects.filter(user=request.user)
    return render(request, 'author/addbook.html', {
        'book': book,
        'books': user_books,
        'mode': 'edit',
    })

def addchapter(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    if request.method == "POST":
        title = request.POST.get("title")
        content = request.POST.get("content")
        if title and content:
            # Auto-increment order
            last_order = book.chapters.aggregate(max_order=Max('order'))['max_order'] or 0
            Chapter.objects.create(
                Book=book,
                title=title,
                content=content,
                order=last_order + 1
            )
            messages.success(request, f'Chapter "{title}"added sucessfully')
            return redirect('abookpage', book_id=book.id)

    return render(request, "author/addchapter.html", {"book": book})



def delete_chapter(request, pk):
    chapter = get_object_or_404(Chapter, pk=pk)
    book = chapter.Book  # the related book instance

    # Delete the chapter
    chapter.delete()

    # Reorder remaining chapters for this book
    chapters = book.chapters.order_by('order')
    for idx, ch in enumerate(chapters, start=1):
        ch.order = idx
        ch.save(update_fields=['order'])

    messages.success(request, "Chapter deleted and reordered successfully.")
    return redirect("abookpage", book_id=book.id)


def edit_chapter(request, chapter_id):
    chapter = get_object_or_404(Chapter, id=chapter_id)
    book = chapter.Book  # get the related book

    if request.method == "POST":
        title = request.POST.get("title")
        content = request.POST.get("content")
        if title and content:
            chapter.title = title
            chapter.content = content
            chapter.save()
            messages.success(request, "Chapter updated successfully.")
            return redirect("abookpage", book_id=book.id)

    return render(request, "author/addchapter.html", {"chapter": chapter, "book": book})

def delete_book(request, pk):
    book = get_object_or_404(Book, id=pk)

    if request.method == 'GET':
        book.delete()
        messages.success(request, f'Book "{book.bname}" deleted successfully!')
        return redirect('create')
