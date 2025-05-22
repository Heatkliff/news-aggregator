from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from datetime import datetime, date
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

    # Handle multiple source filters (OR logic within sources)
    sources_filter = request.GET.getlist('source')
    if sources_filter:
        # Remove empty strings
        sources_filter = [s for s in sources_filter if s]
        if sources_filter:
            news_list = news_list.filter(source__id__in=sources_filter)

    # Handle multiple category filters (OR logic within categories)
    categories_filter = request.GET.getlist('category')
    if categories_filter:
        # Remove empty strings
        categories_filter = [c for c in categories_filter if c]
        if categories_filter:
            news_list = news_list.filter(site_categories__category__slug__in=categories_filter)

    # Handle multiple tag filters (OR logic within tags)
    tags_filter = request.GET.getlist('tag')
    if tags_filter:
        # Remove empty strings
        tags_filter = [t for t in tags_filter if t]
        if tags_filter:
            news_list = news_list.filter(tags__slug__in=tags_filter)

    # Handle date range filtering
    date_range = request.GET.get('date_range')
    if date_range:
        try:
            # Handle single date or date range
            if ' to ' in date_range:
                # Date range
                start_date_str, end_date_str = date_range.split(' to ')
                start_date = datetime.strptime(start_date_str.strip(), '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str.strip(), '%Y-%m-%d').date()
                
                # Filter by date range (inclusive)
                news_list = news_list.filter(
                    created_at__date__gte=start_date,
                    created_at__date__lte=end_date
                )
            else:
                # Single date
                single_date = datetime.strptime(date_range.strip(), '%Y-%m-%d').date()
                news_list = news_list.filter(created_at__date=single_date)
        except (ValueError, AttributeError):
            # Invalid date format, ignore filter
            pass

    # Get data for filter dropdowns
    sources = Source.objects.filter(active=True).order_by('name')
    categories = Category.objects.all().order_by('name')
    tags = Tag.objects.all().order_by('name')

    # Handle sorting (by datetime)
    sort_by = request.GET.get('sort', '-created_at')
    allowed_sorts = ['created_at', '-created_at']
    if sort_by not in allowed_sorts:
        sort_by = '-created_at'

    news_list = news_list.distinct().order_by(sort_by)

    # Pagination
    paginator = Paginator(news_list, 10)  # Show 10 news per page
    page = request.GET.get('page', 1)
    news_list = paginator.get_page(page)
    
    context = {
        'news_list': news_list,
        'sources': sources,
        'categories': categories,
        'tags': tags,
        'current_filters': {
            'sources': sources_filter,
            'categories': categories_filter,
            'tags': tags_filter,
            'date_range': date_range,
            'sort': sort_by,
            'query': query
        }
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