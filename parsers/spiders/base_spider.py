import scrapy
import json
import os
from datetime import datetime
from abc import ABC, abstractmethod
from scrapy.utils.project import get_project_settings
from typing import List, Dict, Any, Optional
import django
import sys

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'news_aggregator.settings')
django.setup()

from news.models import Category, Source, Tag


class BaseNewsSpider(scrapy.Spider, ABC):
    """
    Base spider class for news scraping.
    All site-specific spiders should inherit from this class.
    """
    name = 'base_news_spider'
    
    def __init__(self, source_id=None, *args, **kwargs):
        super(BaseNewsSpider, self).__init__(*args, **kwargs)
        self.source_id = source_id
        self.source = None
        self.categories_map = {}
        self._load_categories()
        
        if source_id:
            try:
                self.source = Source.objects.get(id=source_id)
                self.name = f"{self.name}_{self.source.name.lower().replace(' ', '_')}"
                self.start_urls = [self.source.url]
            except Source.DoesNotExist:
                self.logger.error(f"Source with ID {source_id} does not exist.")
                raise ValueError(f"Source with ID {source_id} does not exist.")
    
    def _load_categories(self):
        """Load all categories from database and prepare for mapping"""
        self.categories = {category.slug: category.id for category in Category.objects.all()}
        
    @abstractmethod
    def parse(self, response):
        """This method must be implemented by all subclasses"""
        pass
    
    @abstractmethod
    def parse_article(self, response):
        """This method must be implemented by all subclasses"""
        pass
    
    def get_category_id(self, category_name: str) -> Optional[int]:
        """
        Get category ID based on site-specific category mapping
        
        Args:
            category_name: The category name as found on the website
            
        Returns:
            Category ID if found, None otherwise
        """
        if not hasattr(self, 'site_categories_map'):
            self.logger.warning("site_categories_map not defined in spider")
            return None
            
        normalized_name = category_name.lower().strip()
        
        if normalized_name in self.site_categories_map:
            category_slug = self.site_categories_map[normalized_name]
            return self.categories.get(category_slug)
        
        return None
    
    def get_output_filename(self):
        """Generate filename for JSON output"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        source_name = "unknown"
        if self.source:
            source_name = self.source.name.lower().replace(' ', '_')
        return f"scraped_{source_name}_{timestamp}.json"
