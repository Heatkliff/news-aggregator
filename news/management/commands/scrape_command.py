import os
import sys
import logging
from django.core.management.base import BaseCommand
from news.models import Source


class Command(BaseCommand):
    """
    Management command to scrape news from configured sources
    """
    help = 'Scrape news from sources marked for scraping'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--source-id',
            type=int,
            help='ID of a specific source to scrape',
        )
    
    def handle(self, *args, **options):
        self.stdout.write('Starting news scraping')
        
        # Add the project directory to the Python path
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
        
        # Import here to avoid circular imports
        from parsers.crawler import run_spider, run_all_spiders
        
        source_id = options.get('source_id')
        
        if source_id:
            try:
                source = Source.objects.get(id=source_id)
                self.stdout.write(f'Scraping specific source: {source.name}')
                success = run_spider(source)
                if success:
                    self.stdout.write(self.style.SUCCESS(f'Successfully scraped: {source.name}'))
                else:
                    self.stdout.write(self.style.ERROR(f'Failed to scrape: {source.name}'))
            except Source.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Source with ID {source_id} does not exist'))
        else:
            self.stdout.write('Scraping all sources marked for scraping')
            run_all_spiders()
            self.stdout.write(self.style.SUCCESS('Successfully completed scraping process'))
