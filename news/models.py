import uuid

from django.db import models
from .utils import slugify


class BaseModel(models.Model):
    """
    Abstract base model with common methods for all models
    """
    class Meta:
        abstract = True
        
    @classmethod
    def get_field_max_length(cls, field_name):
        """
        Get max_length value for a specified field
        """
        return cls._meta.get_field(field_name).max_length

    @classmethod
    def truncate_for_field(cls, value, field_name):
        """
        Truncate value according to field's max_length
        """
        if not value:
            return value
            
        max_length = cls.get_field_max_length(field_name)
        if len(value) > max_length:
            return value[:max_length]
        return value
        
    @classmethod
    def get_safe_slug(cls, text, slug_field='slug'):
        """
        Generate safe slug according to field's max_length
        """
        if not text:
            return ""
            
        base_slug = slugify(text)
        max_length = cls.get_field_max_length(slug_field)
        
        if len(base_slug) > max_length:
            return base_slug[:max_length]
        return base_slug


class Source(BaseModel):
    """
    Model representing a news source (website/publisher)
    """
    name = models.CharField(max_length=255, unique=True)
    url = models.URLField()
    rss_url = models.URLField(blank=True, null=True)
    needs_scraping = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Category(BaseModel):
    """
    Model representing a news category
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=150, unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.get_safe_slug(self.name)

        super().save(*args, **kwargs)


class SiteCategory(BaseModel):
    """
    Model representing an original news category from source
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=150, unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name="site_categories")

    class Meta:
        verbose_name = "Site Category"
        verbose_name_plural = "Site Categories"

    def __str__(self):
        return self.name
        
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.get_safe_slug(self.name)

        super().save(*args, **kwargs)


class News(BaseModel):
    """
    Model representing a news article
    """
    title = models.CharField(max_length=500)
    slug = models.SlugField(max_length=500, unique=True, blank=True)
    content = models.TextField(max_length=5000)
    url = models.URLField(max_length=500)
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='news')
    site_categories = models.ManyToManyField(SiteCategory, related_name='news', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "News"

    def save(self, *args, **kwargs):
        # Ensure fields are within limits
        if self.title:
            self.title = self.truncate_for_field(self.title, 'title')
            
        if self.content:
            self.content = self.truncate_for_field(self.content, 'content')
            
        if self.url:
            self.url = self.truncate_for_field(self.url, 'url')
        
        if not self.slug:
            base_slug = self.get_safe_slug(self.title)

            # If slug is empty after slugify, use UUID
            if not base_slug:
                base_slug = f"news-{str(uuid.uuid4())[:8]}"
                # Make sure it's within limits
                self.slug = self.truncate_for_field(base_slug, 'slug')
            else:
                self.slug = base_slug

        super().save(*args, **kwargs)


class Tag(BaseModel):
    """
    Model representing a tag for news article
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=150, unique=True)
    news = models.ManyToManyField(News, related_name='tags', blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.truncate_for_field(self.name, 'name')
            
        if not self.slug:
            self.slug = self.get_safe_slug(self.name)

        super().save(*args, **kwargs)
