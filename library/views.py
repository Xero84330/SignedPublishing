
from django.shortcuts import render, redirect, get_object_or_404
from .models import Library, History, Collection
from author.models import Book

def library_home(request):
    library, _ = Library.objects.get_or_create(user=request.user)
    history = History.objects.filter(library=library).order_by('-last_read_time')[:15]
    collection = Collection.objects.filter(library=library).order_by('-added_at')[:100]
    
    return render(request, 'reader/library.html', {
        'history': history,
        'collection': collection,
    })

def remove_from_collection(request, book_id):
    library = get_object_or_404(Library, user=request.user)
    Collection.objects.filter(library=library, book_id=book_id).delete()
    return redirect('library')
