import os
import random
import uuid
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify
from django.conf import settings
from news.models import Source, Category, News, Tag
from django.core.management import call_command
from faker import Faker

class Command(BaseCommand):
    """
    Management command to populate the database with test data.
    """
    help = 'Populates the database with test data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--news_count',
            type=int,
            default=50,
            help='Number of news articles to create (default: 50)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before populating'
        )

    def handle(self, *args, **options):
        news_count = options['news_count']
        clear_data = options['clear']
        
        # Initialize faker
        fake = Faker()
        
        # Clear existing data if requested
        if clear_data:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            News.objects.all().delete()
            Tag.objects.all().delete()
            Category.objects.all().delete()
            Source.objects.all().delete()
        
        # Load fixtures
        fixtures_path = os.path.join(settings.BASE_DIR, 'news', 'fixtures')
        
        self.stdout.write(self.style.SUCCESS('Loading categories...'))
        call_command('loaddata', os.path.join(fixtures_path, 'categories.json'))
        
        self.stdout.write(self.style.SUCCESS('Loading sources...'))
        call_command('loaddata', os.path.join(fixtures_path, 'sources.json'))
        
        self.stdout.write(self.style.SUCCESS('Loading tags...'))
        call_command('loaddata', os.path.join(fixtures_path, 'tags.json'))
        
        # Get all loaded data
        sources = list(Source.objects.all())
        categories = list(Category.objects.all())
        tags = list(Tag.objects.all())
        
        if not sources or not categories or not tags:
            self.stdout.write(self.style.ERROR('Error loading fixtures. Please check your JSON files.'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'Creating {news_count} random news articles...'))
        
        # Create news articles
        for i in range(news_count):
            # Generate a random date within the last year
            random_date = timezone.now() - timedelta(days=random.randint(0, 365))
            
            # Create a random title
            title = fake.sentence(nb_words=random.randint(5, 12))
            
            # Generate a unique slug
            base_slug = slugify(title)
            slug = base_slug
            
            # Make sure the slug is unique
            if News.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{str(uuid.uuid4())[:8]}"
            
            # Create random content
            paragraphs = random.randint(3, 10)
            content = '\n\n'.join(fake.paragraphs(nb=paragraphs))
            
            # Create a random URL
            source = random.choice(sources)
            url = f"{source.url}/article/{base_slug}-{random.randint(1000, 9999)}"
            
            # Create the news article
            news = News.objects.create(
                title=title,
                slug=slug,
                content=content,
                url=url,
                source=source,
                created_at=random_date
            )
            
            # Add random categories (1-3)
            random_categories = random.sample(categories, random.randint(1, min(3, len(categories))))
            news.categories.set(random_categories)
            
            # Add random tags (2-5)
            random_tags = random.sample(tags, random.randint(2, min(5, len(tags))))
            news.tags.set(random_tags)
            
            self.stdout.write(f'Created news #{i+1}: {title}')
        
        self.stdout.write(self.style.SUCCESS(f'Successfully populated database with {news_count} news articles'))
