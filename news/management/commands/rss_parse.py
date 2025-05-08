import json
import os

import redis
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from parsers.rss.rss import run_rss_parser


class Command(BaseCommand):
    """
    Management command to parse RSS feeds and save the results to Redis (default) or a JSON file
    """
    help = 'Parse RSS feeds from active sources and save results to Redis or JSON'

    def add_arguments(self, parser):
        """
        Add command line arguments
        """
        parser.add_argument(
            '--json',
            action='store_true',
            help='Save results to a JSON file instead of Redis'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='rss_parsed_news.json',
            help='Path to the output JSON file (only used with --json)'
        )
        parser.add_argument(
            '--redis-key',
            type=str,
            default='rss_parsed_news',
            help='Redis key to store the parsed articles (only used with Redis storage)'
        )

    def save_to_json(self, articles, output_file):
        """
        Save articles to a JSON file
        
        Args:
            articles (list): List of article dictionaries to save
            output_file (str): Path to the output JSON file
        """
        # If the output path is not absolute, make it relative to the project base
        if not os.path.isabs(output_file):
            output_file = os.path.join(settings.BASE_DIR, output_file)
            
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=4)
        self.stdout.write(
            self.style.SUCCESS(f"Results saved to JSON file: {output_file}")
        )

    def save_to_redis(self, articles, redis_key):
        """
        Save articles to Redis
        
        Args:
            articles (list): List of article dictionaries to save
            redis_key (str): Redis key to store the articles
        """
        try:
            # Get Redis connection parameters from settings
            redis_host = getattr(settings, 'REDIS_HOST', 'localhost')
            redis_port = getattr(settings, 'REDIS_PORT', 6379)
            redis_db = getattr(settings, 'REDIS_DB', 0)

            # Connect to Redis
            r = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=False
            )

            # Save articles to Redis
            r.set(redis_key, json.dumps(articles, ensure_ascii=False))
            self.stdout.write(
                self.style.SUCCESS(f"Results saved to Redis with key: {redis_key}")
            )
        except Exception as e:
            raise CommandError(f"Error saving to Redis: {str(e)}")

    def handle(self, *args, **options):
        """
        Execute the command
        """
        use_json = options['json']
        output_file = options['output']
        redis_key = options['redis_key']

        self.stdout.write(self.style.SUCCESS(f"Starting RSS parsing..."))

        try:
            sources, articles = run_rss_parser()

            if sources == 0:
                self.stdout.write(self.style.WARNING("No sources were processed."))
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully processed {sources} source(s) and found {len(articles)} article(s)"
                    )
                )

            # Save articles to JSON file or Redis if there are any
            if articles:
                if use_json:
                    self.save_to_json(articles, output_file)
                else:
                    self.save_to_redis(articles, redis_key)
            else:
                self.stdout.write(self.style.WARNING("No articles found, data not saved"))

        except Exception as e:
            raise CommandError(f"Error during RSS parsing: {str(e)}")
