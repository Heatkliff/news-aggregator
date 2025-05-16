import uuid

from django.db import models
from django.utils.text import slugify as django_slugify


def slugify(text):
    """
    Custom slugify function that handles cyrillic characters by transliterating them to latin
    """
    # Transliteration mapping
    cyrillic_mapping = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'ґ': 'g', 'д': 'd', 'е': 'e',
        'є': 'ye', 'ж': 'zh', 'з': 'z', 'и': 'y', 'і': 'i', 'ї': 'yi', 'й': 'y',
        'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r',
        'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch',
        'ш': 'sh', 'щ': 'shch', 'ь': '', 'ю': 'yu', 'я': 'ya',
        'э': 'e', 'ы': 'y', 'ъ': '', 'ё': 'yo',
    }

    # Convert text to lowercase
    text = text.lower()

    # Replace Cyrillic characters with their Latin equivalents
    for cyrillic, latin in cyrillic_mapping.items():
        text = text.replace(cyrillic, latin)

    # Use Django's slugify for the rest of the processing
    return django_slugify(text)


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
    slug = models.SlugField(max_length=150, unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            # Generate slug with custom slugify function with Cyrillic support
            base_slug = slugify(self.name)

            # Ensure slug is not too long - get max_length from the field itself
            max_length = self._meta.get_field('slug').max_length
            if len(base_slug) > max_length:
                base_slug = base_slug[:max_length]

            self.slug = base_slug

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
        if not self.slug:
            # Generate slug with custom slugify function with Cyrillic support
            base_slug = slugify(self.title)

            # If slug is empty after slugify, use UUID
            if not base_slug:
                base_slug = f"news-{str(uuid.uuid4())[:8]}"

            # Ensure slug is not too long - get max_length from the field itself
            max_length = self._meta.get_field('slug').max_length
            if len(base_slug) > max_length:
                base_slug = base_slug[:max_length]

            self.slug = base_slug

        super().save(*args, **kwargs)


class Tag(models.Model):
    """
    Model representing a tag for news article
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=150, unique=True)
    news = models.ManyToManyField(News, related_name='tags', blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            # Generate slug with custom slugify function with Cyrillic support
            base_slug = slugify(self.name)

            # Ensure slug is not too long - get max_length from the field itself
            max_length = self._meta.get_field('slug').max_length
            if len(base_slug) > max_length:
                base_slug = base_slug[:max_length]

            self.slug = base_slug

        super().save(*args, **kwargs)
