from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Max
from datetime import datetime
import calendar
from datetime import datetime, timedelta
from django.db.models import Sum
from django.shortcuts import render, get_object_or_404
from .models import Book, Chapter, Comment, ChapterViewLog, ChapterLikeLog
from library.models import Collection
from django.utils import timezone
from moderator.models import News


def statistics(request, book_id):
    book = get_object_or_404(Book, id=book_id, user=request.user)
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)

    # --- TODAY'S STATS (using logs) ---
    today_views = ChapterViewLog.objects.filter(
        chapter__Book=book,
        viewed_at__date=today
    ).count()

    today_likes = ChapterLikeLog.objects.filter(
        chapter__Book=book,
        liked_at__date=today
    ).count()

    today_comments = Comment.objects.filter(
        chapter__Book=book,
        created_at__date=today
    ).count()

    today_bookmarks = Collection.objects.filter(
        book=book,
        added_at__date=today
    ).count()

    # --- YESTERDAY'S STATS ---
    yesterday_views = ChapterViewLog.objects.filter(
        chapter__Book=book,
        viewed_at__date=yesterday
    ).count()

    yesterday_likes = ChapterLikeLog.objects.filter(
        chapter__Book=book,
        liked_at__date=yesterday
    ).count()

    yesterday_comments = Comment.objects.filter(
        chapter__Book=book,
        created_at__date=yesterday
    ).count()

    # --- TOTAL BOOKMARKS (real count) ---
    total_bookmarks = Collection.objects.filter(book=book).count()

    # --- GROWTH CALCULATION ---
    def calc_growth(today_val, yesterday_val):
        if yesterday_val == 0:
            return 100 if today_val > 0 else 0
        return round(((today_val - yesterday_val) / yesterday_val) * 100, 1)

    view_growth = calc_growth(today_views, yesterday_views)
    like_growth = calc_growth(today_likes, yesterday_likes)
    comment_growth = calc_growth(today_comments, yesterday_comments)

    # --- LAST 7 DAYS DATA (for charts) ---
    daily_labels = []
    daily_views = []
    daily_likes = []
    daily_comments = []
    daily_bookmarks = []
    daily_engagement = []

    update_dates = [
        chap.created_at.day
        for chap in book.chapters.all()
        if chap.created_at.month == today.month and chap.created_at.year == today.year
    ]

    for i in range(6, -1, -1):  # 7 days, today first
        day = today - timedelta(days=i)
        label = day.strftime("%b %d")

        views = ChapterViewLog.objects.filter(
            chapter__Book=book,
            viewed_at__date=day
        ).count()

        likes = ChapterLikeLog.objects.filter(
            chapter__Book=book,
            liked_at__date=day
        ).count()

        comments = Comment.objects.filter(
            chapter__Book=book,
            created_at__date=day
        ).count()

        bookmarks = Collection.objects.filter(
            book=book,
            added_at__date=day
        ).count()

        daily_labels.append(label)
        daily_views.append(views)
        daily_likes.append(likes)
        daily_comments.append(comments)
        daily_bookmarks.append(bookmarks)
        daily_engagement.append(views + likes + comments + bookmarks)

    # --- ENGAGEMENT SUMMARY ---
    engagement_data = {
        "views": today_views,
        "likes": today_likes,
        "comments": today_comments,
        "bookmarks": today_bookmarks,
    }

    # --- TOP CHAPTERS ---
    top_chapters = book.chapters.annotate(
        total_interactions=Sum('views') + Sum('likes')
    ).order_by('-total_interactions')[:5]

    # --- CONTEXT ---
    context = {
        "book": book,
        "today_views": today_views,
        "today_likes": today_likes,
        "today_comments": today_comments,
        "today_bookmarks": today_bookmarks,
        "total_bookmark": total_bookmarks,  # Fixed!
        "view_growth": view_growth,
        "like_growth": like_growth,
        "comment_growth": comment_growth,
        "total_engagement": sum(engagement_data.values()),
        "top_chapters": top_chapters,
        "daily_labels": daily_labels,
        "daily_views": daily_views,
        "daily_likes": daily_likes,
        "daily_comments": daily_comments,
        "daily_bookmarks": daily_bookmarks,
        "daily_engagement": daily_engagement,
        "engagement_data": engagement_data,
        "update_dates": update_dates,
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
        bname = request.POST.get('bname')
        btype = request.POST.get('btype')
        genre = request.POST.get('genre')
        agerating = request.POST.get('agerating')
        description = request.POST.get('description')
        coverimage = request.FILES.get('coverimage')

        # Tie the book to the logged-in user
        Book.objects.create(
            user=request.user,
            bname=bname,
            btype=btype,
            genre=genre,
            agerating=agerating,
            description=description,
            coverimage=coverimage
        )
        messages.success(request, f'Book "{bname}" has been created successfully!')
        return redirect('create')

    # Show books belonging to logged-in user
    user_books = Book.objects.filter(user=request.user)
    return render(request, 'author/addbook.html', {'books': user_books})


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

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from .models import Chapter

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
