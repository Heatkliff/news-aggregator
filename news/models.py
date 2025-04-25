import uuid

from django.db import models
from django.utils.text import slugify


class Source(models.Model):
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


class Category(models.Model):
    """
    Model representing a news category
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class SiteCategory(models.Model):
    """
    Model representing an original news category from source
    """
    name = models.CharField(max_length=100, unique=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name="site_categories")

    class Meta:
        verbose_name = "Site Category"
        verbose_name_plural = "Site Categories"

    def __str__(self):
        return self.name


class News(models.Model):
    """
    Model representing a news article
    """
    title = models.CharField(max_length=500)
    slug = models.SlugField(max_length=500, unique=True, blank=True)
    content = models.TextField()
    url = models.URLField(unique=True)
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='news')
    site_categories = models.ManyToManyField(SiteCategory, related_name='news', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "News"

    def save(self, *args, **kwargs):
        if not self.slug:
            # Generate unique slug
            self.slug = slugify(self.title)
            # If slug already exists, append a UUID to make it unique
            if News.objects.filter(slug=self.slug).exists():
                self.slug = f"{self.slug}-{str(uuid.uuid4())[:8]}"
        super().save(*args, **kwargs)


class Tag(models.Model):
    """
    Model representing a tag for news article
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    news = models.ManyToManyField(News, related_name='tags', blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
