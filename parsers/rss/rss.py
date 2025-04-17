import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import feedparser
import requests
from bs4 import BeautifulSoup
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

            # Extract full content based on the source
            content = self._extract_full_content(entry, url, source.name)

            # Leave slug empty as requested
            slug = ""

            # Get site category (single value, not a list)
            site_category = ""
            if hasattr(entry, 'tags'):
                for tag in entry.tags:
                    if hasattr(tag, 'term') and tag.term:
                        site_category = tag.term.strip()
                        break
            elif hasattr(entry, 'category'):
                if isinstance(entry.category, list) and entry.category:
                    site_category = entry.category[0].strip() if entry.category[0] else ""
                elif entry.category:
                    site_category = entry.category.strip()

            # Create SiteCategory if not empty
            if site_category:
                category_obj, _ = SiteCategory.objects.get_or_create(name=site_category)
                site_category = category_obj.name

            # Get tags - extract all possible tags from the entry
            tags = []

            # Special handling for Korrespondent source
            if source.name == 'Кореспондент' or 'korrespondent.net' in url:
                # Check if entry has content that might contain orgsource:tags
                content_to_check = ""
                if hasattr(entry, 'content') and entry.content:
                    content_to_check = entry.content[0].value if isinstance(entry.content[0].value, str) else ""
                elif hasattr(entry, 'description'):
                    content_to_check = entry.description
                elif hasattr(entry, 'summary'):
                    content_to_check = entry.summary

                # Extract tags from <orgsource:tags> format
                if content_to_check:
                    tag_match = re.search(r'<orgsource:tags>(.*?)</orgsource:tags>', content_to_check)
                    if tag_match:
                        raw_tags = tag_match.group(1)
                        # Split by commas and strip whitespace
                        tags = [tag.strip() for tag in raw_tags.split(',') if tag.strip()]
                        logger.info(f"Extracted tags from Korrespondent: {tags}")

            # If tags are still empty, use standard extraction methods
            if not tags:
                if hasattr(entry, 'tags'):
                    tags = [tag.term.strip() for tag in entry.tags if hasattr(tag, 'term') and tag.term.strip()]
                elif hasattr(entry, 'category'):
                    if isinstance(entry.category, list):
                        tags = [cat.strip() for cat in entry.category if cat and cat.strip()]
                    elif entry.category and entry.category.strip():
                        tags = [entry.category.strip()]

            # Set created_at as the current moment of parsing
            current_time = datetime.now().isoformat()

            # Create article dictionary
            article = {
                "title": title,
                "slug": slug,
                "content": content,
                "url": url,
                "source": source.name,
                "site_category": site_category,
                "tags": tags,
                "created_at": current_time
            }

            return article

        except Exception as e:
            logger.error(f"Error processing entry: {str(e)}")
            return None

    def _extract_full_content(self, entry, url: str, source_name: str) -> str:
        """
        Extract full content from the entry or article page based on the source

        Args:
            entry: RSS feed entry
            url: Article URL
            source_name: Name of the source

        Returns:
            Cleaned full content of the article
        """
        content = ""
        domain = urlparse(url).netloc

        # First check common RSS fields
        if hasattr(entry, 'content_encoded'):
            content = entry.content_encoded
        elif hasattr(entry, 'content') and entry.content:
            content = entry.content[0].value
        elif hasattr(entry, 'fulltext'):
            content = entry.fulltext

        # If not found in common fields, check source-specific locations
        if not content:
            # Look for content:encoded field (used by some WordPress sites)
            for key in entry.keys():
                if key.endswith('encoded') and key != 'comments_encoded':
                    content = entry[key]
                    break

        # If still no content, fall back to summary or description
        if not content and hasattr(entry, 'summary'):
            content = entry.summary
        elif not content and hasattr(entry, 'description'):
            content = entry.description

        # Source-specific extraction and cleaning
        if 'korrespondent.net' in domain or source_name == 'Кореспондент':
            # For Korrespondent, try to get fulltext if available
            if hasattr(entry, 'fulltext'):
                content = entry.fulltext

            # Clean content
            content = self._clean_content(content)

        elif 'tsn.ua' in domain or source_name == 'ТСН':
            # For TSN, try to get fulltext if available
            if hasattr(entry, 'fulltext'):
                content = entry.fulltext

            # Clean content
            content = self._clean_content(content)

        elif 'pravda.com.ua' in domain or source_name == 'Українська правда':
            # For Pravda, use content:encoded if available
            for key in entry.keys():
                if key.endswith('encoded') and key != 'comments_encoded':
                    content = entry[key]
                    break

            # Clean content
            content = self._clean_content(content)

        # For other sources, clean whatever content we have
        return self._clean_content(content)

    def _clean_content(self, content: str) -> str:
        """
        Clean article content from HTML tags and other unwanted elements

        Args:
            content: Raw article content

        Returns:
            Cleaned content
        """
        if not content:
            return ""

        # Remove CDATA markers
        content = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', content, flags=re.DOTALL)

        # Use BeautifulSoup to extract text
        soup = BeautifulSoup(content, 'html.parser')

        # Remove script and style elements
        for element in soup(["script", "style"]):
            element.decompose()

        # Get text
        text = soup.get_text(separator=" ")

        # Remove extra spaces, tabs, and newlines
        text = re.sub(r'\s+', ' ', text).strip()

        # Remove common patterns like "Read also: "
        text = re.sub(r'Читайте також:.*?(?=\.|$)', '', text)

        return text


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