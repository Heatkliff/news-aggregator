from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from .models import News, Source, Category, Tag

def index(request):
    """
    View for the main page displaying the list of news articles
    with filtering and search functionality
    """
    # Default sorting by newest first
    news_list = News.objects.all().order_by('-created_at')
    
    # Handle search query
    query = request.GET.get('q')
    if query:
        news_list = news_list.filter(
            Q(title__icontains=query) | 
            Q(content__icontains=query)
        )

    source = request.GET.get('source')
    if source:
        news_list = news_list.filter(source__id=source)

    category = request.GET.get('category')
    if category:
        news_list = news_list.filter(site_categories__category__slug=category)

    tag = request.GET.get('tag')
    if tag:
        news_list = news_list.filter(tags__slug=tag)

    # Get data for filter dropdowns
    sources = Source.objects.filter(active=True)
    categories = Category.objects.all()
    tags = Tag.objects.all()
    
    # Pagination
    paginator = Paginator(news_list, 10)  # Show 10 news per page
    page = request.GET.get('page', 1)
    news_list = paginator.get_page(page)
    
    context = {
        'news_list': news_list,
        'sources': sources,
        'categories': categories,
        'tags': tags,
    }
    
    return render(request, 'news/index.html', context)

def news_detail(request, slug):
    """
    View for displaying the details of a specific news article
    """
    news = get_object_or_404(News, slug=slug)
    
    # Get related news (same source or categories)
    related_news = News.objects.filter(
        Q(source=news.source) | 
        Q(site_categories__in=news.site_categories.all())
    ).exclude(id=news.id).distinct().order_by('-created_at')[:5]
    
    context = {
        'news': news,
        'related_news': related_news,
    }
    
    return render(request, 'news/detail.html', context)

def source_list(request):
    """
    View for displaying the list of news sources
    """
    sources = Source.objects.all().order_by('name')
    
    # Pagination
    paginator = Paginator(sources, 10)  # Show 10 sources per page
    page = request.GET.get('page', 1)
    sources = paginator.get_page(page)
    
    context = {
        'sources': sources,
    }
    
    return render(request, 'news/source_list.html', context)
