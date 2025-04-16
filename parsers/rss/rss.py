import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import feedparser
from requests.exceptions import RequestException

from news.models import News, Source, SiteCategory

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class RSSParser:
    """
    Class for parsing RSS feeds from various news sources
    """

    def __init__(self, output_file: str = 'parsed_news.json'):
        """
        Initialize the RSS parser

        Args:
            output_file: Path to the output JSON file
        """
        self.output_file = output_file

    def parse_all_active_sources(self) -> Tuple[int, int]:
        """
        Parse all active sources with RSS URLs from the database

        Returns:
            Tuple containing count of processed sources and new articles
        """
        active_sources = Source.objects.filter(active=True).exclude(rss_url__isnull=True).exclude(rss_url='')

        if not active_sources:
            logger.warning("No active sources with RSS URLs found in the database")
            return 0, 0

        total_sources = active_sources.count()
        total_articles = 0
        all_articles = []

        for source in active_sources:
            logger.info(f"Processing source: {source.name}")
            articles, count = self.parse_source(source)
            if articles:
                all_articles.extend(articles)
                total_articles += count

        # Save all articles to JSON file
        if all_articles:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(all_articles, f, ensure_ascii=False, indent=4)
            logger.info(f"Saved {len(all_articles)} articles to {self.output_file}")
        else:
            logger.warning("No articles parsed, JSON file not created")

        return total_sources, total_articles

    # Removed predefined_sources method as we're only using sources from the database

    def parse_source(self, source: Source) -> Tuple[List[Dict], int]:
        """
        Parse RSS feed for a specific source

        Args:
            source: Source model instance

        Returns:
            Tuple containing list of parsed articles and count of new articles
        """
        try:
            logger.info(f"Fetching RSS feed from: {source.rss_url}")
            feed = feedparser.parse(source.rss_url)

            if hasattr(feed, 'bozo_exception'):
                logger.error(f"Error parsing feed {source.name}: {feed.bozo_exception}")
                return [], 0

            if not feed.entries:
                logger.warning(f"No entries found in feed: {source.name}")
                return [], 0

            articles = []
            count = 0

            for entry in feed.entries:
                article = self._process_entry(entry, source)
                if article:
                    articles.append(article)
                    count += 1

            logger.info(f"Parsed {count} articles from {source.name}")
            return articles, count

        except RequestException as e:
            logger.error(f"Request error for {source.name}: {str(e)}")
            return [], 0
        except Exception as e:
            logger.error(f"Error parsing {source.name}: {str(e)}")
            return [], 0

    def _process_entry(self, entry, source: Source) -> Optional[Dict]:
        """
        Process a single RSS entry and convert to article dict

        Args:
            entry: RSS feed entry
            source: Source model instance

        Returns:
            Dictionary containing article data or None if processing failed
        """
        try:
            # Extract URL
            url = entry.link if hasattr(entry, 'link') else None
            if not url:
                logger.warning("Entry has no URL, skipping")
                return None

            # Check if this URL already exists in the database
            if News.objects.filter(url=url).exists():
                logger.debug(f"Article with URL {url} already exists, skipping")
                return None

            # Extract title
            title = entry.title if hasattr(entry, 'title') else "Untitled"

            # Extract content
            content = ""
            if hasattr(entry, 'content') and entry.content:
                content = entry.content[0].value
            elif hasattr(entry, 'summary'):
                content = entry.summary
            elif hasattr(entry, 'description'):
                content = entry.description

            # Leave slug empty as requested
            slug = ""

            # Get categories
            categories = []
            if hasattr(entry, 'tags'):
                categories = [tag.term for tag in entry.tags if hasattr(tag, 'term')]
            elif hasattr(entry, 'category'):
                if isinstance(entry.category, list):
                    categories = entry.category
                else:
                    categories = [entry.category]

            # Process categories - create if they don't exist
            site_categories = []
            for category_name in categories:
                if category_name and category_name.strip():
                    category, _ = SiteCategory.objects.get_or_create(name=category_name.strip())
                    site_categories.append(category.name)

            # Set created_at as the current moment of parsing
            current_time = datetime.now().isoformat()

            # Create article dictionary
            article = {
                "title": title,
                "slug": slug,
                "content": content,
                "url": url,
                "source": source.name,
                "site_categories": site_categories,
                "created_at": current_time
            }

            return article

        except Exception as e:
            logger.error(f"Error processing entry: {str(e)}")
            return None


def run_rss_parser(output_file: str = 'parsed_news.json') -> Tuple[int, int]:
    """
    Run the RSS parser to fetch news articles

    Args:
        output_file: Path to the output JSON file

    Returns:
        Tuple containing count of processed sources and new articles
    """
    parser = RSSParser(output_file)
    return parser.parse_all_active_sources()


if __name__ == "__main__":
    # This allows running the script directly for testing
    sources, articles = run_rss_parser()
    print(f"Processed {sources} sources and found {articles} new articles")
