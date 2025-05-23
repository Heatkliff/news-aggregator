from django.contrib import admin
from .models import Source, Category, SiteCategory, News, Tag, LogStats


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'rss_url', 'needs_scraping', 'active')
    list_filter = ('active', 'needs_scraping')
    search_fields = ('name', 'url')
    date_hierarchy = 'created_at'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(SiteCategory)
class SiteCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    search_fields = ('name',)
    autocomplete_fields = ('category',)

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'source', 'created_at', 'display_tags')
    list_filter = ('source', 'site_categories')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'
    filter_horizontal = ('site_categories', 'tags')
    
    def display_tags(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])
    
    display_tags.short_description = "Tags"


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    filter_horizontal = ('news',)

@admin.register(LogStats)
class ImportStatsAdmin(admin.ModelAdmin):
    list_display = ('started_at', 'completed_at', 'imported', 'skipped', 'errors')