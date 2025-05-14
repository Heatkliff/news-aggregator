import json
import logging
from typing import Dict, List

from django.core.management.base import BaseCommand
from django.db import transaction
import redis

from django.conf import settings

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

            try:
                # Try to parse as a JSON array
                parsed_data = json.loads(data)

                # Check if it's a list with a single item containing a 'value' key
                if parsed_data and isinstance(parsed_data, list) and len(parsed_data) > 0:
                    if isinstance(parsed_data[0], dict) and 'value' in parsed_data[0]:
                        value_content = parsed_data[0]['value']
                        if isinstance(value_content, str):
                            final_data = json.loads(value_content)
                            logger.info(f"Successfully parsed data from Redis: {len(final_data)} items")
                            return final_data
                        else:
                            logger.info(f"Value content is not a string, returning as is")
                            return value_content

                # If structure is different than expected
                logger.info(f"Using default parsing approach")
                if isinstance(parsed_data, list):
                    return parsed_data
                else:
                    # If it's not a list, return it wrapped in a list
                    return [parsed_data]

            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON data: {str(e)}")
                return []

        except Exception as e:
            logger.error(f"Error retrieving data from Redis: {str(e)}")
            return []

    @transaction.atomic
    def import_news(self, key: str = "rss_parsed_news") -> Dict:
        """
        Import news from Redis to the database
        Returns statistics of the import operation
        """
        from ...models import News, Source, SiteCategory, Tag  # Import here to avoid circular imports

        news_data = self.get_news_from_redis(key)
        stats = {"imported": 0, "skipped": 0, "errors": 0}
        if not news_data:
            logger.warning("No news data found to import")
            return stats

        logger.info(f"Found {len(news_data)} news items to process")

        for item in news_data:
            try:
                # Skip if no title
                if not item.get('title'):
                    logger.warning("Skipping item with missing title")
                    stats["skipped"] += 1
                    continue

                logger.info(f"Processing news item: {item.get('title', 'Unknown title')[:50]}...")

                # Skip if news already exists (checking by title)
                if News.objects.filter(title=item['title']).exists():
                    logger.info(f"News already exists: {item['title'][:50]}...")
                    stats["skipped"] += 1
                    continue

                # Get source
                source = Source.objects.get(name=item['source'])

                # Create news with transaction to ensure atomicity
                with transaction.atomic():
                    try:
                        news = News.objects.create(
                            title=item['title'],
                            content=item['content'],
                            url=item['url'],
                            source=source
                        )

                        # Handle site category
                        if 'site_category' in item and item['site_category']:
                            site_category, created = SiteCategory.objects.get_or_create(
                                name=item['site_category'].lower()
                            )
                            news.site_categories.add(site_category)

                        # Handle tags
                        if 'tags' in item and item['tags'] and isinstance(item['tags'], list):
                            for tag_name in item['tags']:
                                if not tag_name:  # Skip empty tag names
                                    continue

                                tag_name = tag_name.lower().strip()

                                # Try to get existing tag or create new one
                                tag, created = Tag.objects.get_or_create(name=tag_name)
                                news.tags.add(tag)

                    except Exception as e:
                        logger.error(f"Database error while saving: {str(e)}", exc_info=True)
                        raise

                stats["imported"] += 1
                logger.info(f"Successfully imported news: {news.title[:50]}...")

            except Exception as e:
                stats["errors"] += 1
                logger.error(f"Error importing news: {str(e)}", exc_info=True)
                logger.debug(f"Problematic data: {item}")

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
            from ...models import News
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
