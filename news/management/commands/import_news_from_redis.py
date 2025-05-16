import json
import logging
from typing import Dict, List, Optional

from django.core.management.base import BaseCommand
from django.db import transaction
import redis

from django.conf import settings
from news.models import News, Source, SiteCategory, Tag

logger = logging.getLogger(__name__)


class NewsImporter:
    """
    Service class responsible for importing news from Redis to the database.
    """

    def __init__(self):
        # Get Redis configuration from settings with fallbacks
        redis_host = getattr(settings, 'REDIS_HOST', 'redis')
        redis_port = getattr(settings, 'REDIS_PORT', 6379)
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, db=0)

    def _parse_redis_data(self, raw_data: bytes) -> List[Dict]:
        """
        Parse raw bytes data from Redis into a list of news items.
        """
        try:
            parsed_data = json.loads(raw_data)

            # Case 1: Direct list of news items
            if isinstance(parsed_data, list) and not (len(parsed_data) > 0 and isinstance(parsed_data[0], dict)
                                                      and 'value' in parsed_data[0]):
                logger.info(f"Parsed data as direct list with {len(parsed_data)} items")
                return parsed_data

            # Case 2: List with 'value' key in first item
            if (isinstance(parsed_data, list) and len(parsed_data) > 0 and isinstance(parsed_data[0], dict)
                    and 'value' in parsed_data[0]):
                value_content = parsed_data[0]['value']

                if isinstance(value_content, str):
                    # Value is a JSON string that needs parsing
                    final_data = json.loads(value_content)
                    logger.info(f"Successfully parsed data from Redis 'value' field: {len(final_data)} items")
                    return final_data
                elif isinstance(value_content, list):
                    # Value is already a list
                    logger.info(f"Using value content directly: {len(value_content)} items")
                    return value_content
                else:
                    # Value is something else, wrap it in a list
                    logger.info(f"Value content is not a string or list, wrapping in list")
                    return [value_content]

            # Case 3: Single object, not a list
            if isinstance(parsed_data, dict):
                logger.info("Parsed data as single object, wrapping in list")
                return [parsed_data]

            # Case 4: Empty or unrecognized format
            logger.warning(f"Unrecognized data format, returning empty list")
            return []

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON data: {str(e)}")
            return []

    def get_news_from_redis(self, key: str = "rss_parsed_news") -> List[Dict]:
        """
        Retrieve news data from Redis
        """
        try:
            logger.info(f"Retrieving data from Redis with key: {key}")
            data = self.redis_client.get(key)

            if not data:
                logger.warning(f"No data found in Redis with key: {key}")
                # Check if similar keys exist
                keys = self.redis_client.keys("*rss_parsed_news*")
                if keys:
                    logger.info(f"Found similar keys in Redis: {keys}")
                return []

            logger.debug(f"Retrieved raw data from Redis")
            return self._parse_redis_data(data)

        except Exception as e:
            logger.error(f"Error retrieving data from Redis: {str(e)}")
            return []

    def _get_or_create_site_category(self, category_name: str) -> Optional[SiteCategory]:
        """
        Get or create a site category
        """
        if not category_name:
            return None

        category_name = category_name.lower().strip()
        category_slug = SiteCategory.get_safe_slug(category_name)

        if not category_slug:
            return None

        site_category, created = SiteCategory.objects.get_or_create(
            slug=category_slug,
            defaults={'name': category_name}
        )

        if created:
            logger.debug(f"Created new site category: {category_name}")

        return site_category

    def _get_or_create_tag(self, tag_name: str) -> Optional[Tag]:
        """
        Get or create a tag
        """
        if not tag_name:
            return None

        tag_name = tag_name.lower().strip()
        tag_slug = Tag.get_safe_slug(tag_name)

        if not tag_slug:
            return None

        try:
            tag, created = Tag.objects.get_or_create(
                slug=tag_slug,
                defaults={'name': tag_name}
            )

            if created:
                logger.debug(f"Created new tag: {tag_name}")

            return tag
        except Exception as e:
            logger.error(f"Error creating tag '{tag_name}' (slug: {tag_slug}): {str(e)}")
            return None

    def _process_single_news_item(self, item: Dict) -> bool:
        """
        Process and save a single news item
        Returns True if import was successful, False otherwise
        """
        # Skip if no title
        if not item.get('title'):
            logger.warning("Skipping item with missing title")
            return False

        logger.info(f"Processing news item: {item.get('title', 'Unknown title')[:50]}...")

        # Generate slug for checking if news already exists
        news_slug = News.get_safe_slug(item['title'])

        # Skip if news already exists (checking by slug)
        if News.objects.filter(slug=news_slug).exists():
            logger.info(f"News already exists with slug: {news_slug[:50]}...")
            return False

        try:
            # Get source
            source = Source.objects.get(name=item['source'])

            # Create the news object
            news = News.objects.create(
                title=item['title'],
                content=item['content'],
                url=item['url'],
                source=source
            )

            # Handle site category
            if 'site_category' in item and item['site_category']:
                site_category = self._get_or_create_site_category(item['site_category'])
                if site_category:
                    news.site_categories.add(site_category)

            # Handle tags
            if 'tags' in item and item['tags'] and isinstance(item['tags'], list):
                for tag_name in item['tags']:
                    tag = self._get_or_create_tag(tag_name)
                    if tag:
                        news.tags.add(tag)

            logger.info(f"Successfully imported news: {news.title[:50]}...")
            return True

        except Source.DoesNotExist:
            logger.error(f"Source not found: {item.get('source')}")
            return False
        except Exception as e:
            logger.error(f"Error importing news: {str(e)}", exc_info=True)
            logger.debug(f"Problematic data: {item}")
            return False

    @transaction.atomic
    def import_news(self, key: str = "rss_parsed_news") -> Dict:
        """
        Import news from Redis to the database
        Returns statistics of the import operation
        """
        news_data = self.get_news_from_redis(key)
        stats = {"imported": 0, "skipped": 0, "errors": 0}

        if not news_data:
            logger.warning("No news data found to import")
            return stats

        logger.info(f"Found {len(news_data)} news items to process")

        for item in news_data:
            try:
                with transaction.atomic():
                    result = self._process_single_news_item(item)
                    if result:
                        stats["imported"] += 1
                    else:
                        stats["skipped"] += 1
            except Exception as e:
                stats["errors"] += 1
                logger.error(f"Unexpected error during news import: {str(e)}", exc_info=True)

        return stats


class Command(BaseCommand):
    """
    Django management command to import news from Redis to PostgreSQL
    """
    help = 'Import news from Redis to PostgreSQL database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--key',
            type=str,
            default="rss_parsed_news",
            help='Redis key containing news data'
        )

        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear Redis data after import'
        )

        parser.add_argument(
            '--delete-existing',
            action='store_true',
            help='Delete all existing news before import (CAUTION: destructive operation)'
        )

    def handle(self, *args, **options):
        redis_key = options['key']
        clear_after_import = options['clear']
        delete_existing = options['delete_existing']

        self.stdout.write(self.style.NOTICE(f"Starting news import from Redis key: {redis_key}"))

        # Optional: Delete all existing news
        if delete_existing:
            count = News.objects.all().count()
            News.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Deleted {count} existing news"))

        importer = NewsImporter()
        stats = importer.import_news(redis_key)

        self.stdout.write(
            self.style.SUCCESS(
                f"News import completed. Imported: {stats['imported']}, "
                f"Skipped: {stats['skipped']}, Errors: {stats['errors']}"
            )
        )

        # Clear Redis after successful import if requested
        if clear_after_import and stats['imported'] > 0:
            importer.redis_client.delete(redis_key)
            self.stdout.write(self.style.SUCCESS(f"Cleared Redis key: {redis_key}"))
