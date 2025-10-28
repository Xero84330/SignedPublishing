from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from authentication.models import User
from author.models import Book
from .models import HighlightedBook
from .models import News
# Staff-only decorator
def staff_required(user):
    return user.is_staff

# Helper function to create a HighlightedBook
def create_highlight(request, book_id, category, order=1):
    book = get_object_or_404(Book, id=book_id)
    if HighlightedBook.objects.filter(book=book, category=category).exists():
        messages.warning(request, f"'{book.bname}' is already in {category} list.")
        return None
    return HighlightedBook.objects.create(
        book=book,
        category=category,
        order=order,
        added_by=request.user
    )

@login_required
@user_passes_test(staff_required)
@login_required
@user_passes_test(staff_required)
def highlight_list(request):
    top_books = HighlightedBook.objects.filter(category=HighlightedBook.CATEGORY_TOP).select_related('book')
    featured_books = HighlightedBook.objects.filter(category=HighlightedBook.CATEGORY_FEATURED).select_related('book')
    news_items = News.objects.all().order_by('-added_on')  # fetch news for dashboard

    return render(request, 'moderator/highlight_list.html', {
        'top_books': top_books,
        'featured_books': featured_books,
        'news_items': news_items,  # pass news to template
    })


@login_required
@user_passes_test(staff_required)
def add_highlight(request):
    if request.method == 'POST':
        book_id = request.POST.get('book_id')
        category = request.POST.get('category')
        order = int(request.POST.get('order', 1))

        if not (book_id and category):
            messages.error(request, "Book and category are required.")
            return redirect('highlight_list')

        highlight = create_highlight(request, book_id, category, order)
        if highlight:
            messages.success(request, f"'{highlight.book.bname}' added to {category} list.")
        return redirect('highlight_list')

    books = Book.objects.all()
    return render(request, 'moderator/add_highlight.html', {'books': books})

@login_required
@user_passes_test(staff_required)
def delete_highlight(request, pk):
    highlight = get_object_or_404(HighlightedBook, pk=pk)
    highlight.delete()
    messages.success(request, f"'{highlight.book.bname}' removed from list.")
    return redirect('highlight_list')

@login_required
@user_passes_test(staff_required)
def reorder_highlight(request):
    if request.method == 'POST':
        new_order = request.POST.getlist('order[]')
        for idx, hb_id in enumerate(new_order, start=1):
            HighlightedBook.objects.filter(id=hb_id).update(order=idx)
        return redirect('highlight_list')
    messages.error(request, "Invalid request")
    return redirect('highlight_list')

@login_required
@user_passes_test(staff_required)
def add_book_page(request):
    # Pre-select category from URL
    selected_category = request.GET.get('category', '')

    if request.method == 'POST':
        book_id = request.POST.get('book_id')
        category = request.POST.get('category')
        order = int(request.POST.get('order', 1))

        if not (book_id and category):
            messages.error(request, "Book and category are required.")
            return redirect('add_book_page')

        highlight = create_highlight(request, book_id, category, order)
        if highlight:
            messages.success(request, f"'{highlight.book.bname}' added to {category} list.")
        return redirect('add_book_page')

    # GET: filter/search books
    search_query = request.GET.get('q', '').strip()
    author_id = request.GET.get('author_id')
    book_id = request.GET.get('book_id', '')

    books = Book.objects.all()
    if search_query:
        books = books.filter(bname__icontains=search_query)
    if author_id:
        books = books.filter(author__id=author_id)
    if book_id:
        books = books.filter(id=book_id)

    authors = User.objects.filter(books__isnull=False).distinct()

    return render(request, 'moderator/add_highlight.html', {
        'books': books,
        'authors': authors,
        'search_query': search_query,
        'selected_author': int(author_id) if author_id else None,
        'book_id': book_id,
        'selected_category': selected_category,
    })

@login_required
@user_passes_test(staff_required)
def news_list(request):
    news_items = News.objects.all()
    return render(request, 'moderator/news_list.html', {'news_items': news_items})

@login_required
@user_passes_test(staff_required)
def add_news(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        image = request.FILES.get('image')

        if not title or not content:
            messages.error(request, "Title and content are required.")
            return redirect('add_news')

        News.objects.create(
            title=title,
            content=content,
            image=image,
            added_by=request.user
        )
        messages.success(request, "News added successfully.")
        return redirect('highlight_list')

    return render(request, 'moderator/add_news.html')

@login_required
@user_passes_test(staff_required)
def delete_news(request, pk):
    news_item = get_object_or_404(News, pk=pk)
    news_item.delete()
    return redirect('highlight_list') 