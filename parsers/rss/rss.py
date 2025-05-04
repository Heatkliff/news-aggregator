import logging
import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import feedparser
from bs4 import BeautifulSoup
from requests.exceptions import RequestException

from news.models import News, Source

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class RSSParser:
    """
    Class for parsing RSS feeds from various news sources using a configuration-based approach
    """

    # Site configurations
    SITE_CONFIGS = {
        "default": {
            "name": "Default",
            "domain_patterns": [],
            "content_extractors": [
                lambda entry: entry.get('content_encoded', ''),
                lambda entry: entry.get('content', [{}])[0].get('value', '') if entry.get('content') else '',
                lambda entry: entry.get('fulltext', ''),
                lambda entry: entry.get('summary', ''),
                lambda entry: entry.get('description', '')
            ],
            "tag_extractors": [
                lambda entry: [tag.strip() for key, val in entry.items() if 'tags' in key.lower() and
                               isinstance(val, str) for tag in val.split(',') if tag.strip()],
                lambda entry: [tag.term.strip() for tag in entry.get('tags', []) if
                               hasattr(tag, 'term') and tag.term.strip()],
                lambda entry: [entry.get('category', '').strip()] if entry.get('category') and
                                                                     isinstance(entry.get('category'), str) else [],
                lambda entry: [cat.strip() for cat in entry.get('category', []) if cat and cat.strip()] if
                isinstance(entry.get('category'), list) else []
            ],
            "category_extractors": [
                lambda entry: entry.get('category', '').strip() if isinstance(entry.get('category'), str) else '',
                lambda entry: entry.get('category', [''])[0].strip() if isinstance(entry.get('category'), list) and
                                                                        entry.get('category') else ''
            ],
            "content_cleaners": []
        }
    }

    def __init__(self):
        """
        Initialize the RSS parser
        """
        pass

    def parse_all_active_sources(self) -> Tuple[int, List[Dict]]:
        """
        Parse all active sources with RSS URLs from the database

        Returns:
            Tuple containing count of processed sources and list of parsed articles
        """
        active_sources = Source.objects.filter(active=True).exclude(rss_url__isnull=True).exclude(rss_url='')

        if not active_sources:
            logger.warning("No active sources with RSS URLs found in the database")
            return 0, []

        total_sources = active_sources.count()
        all_articles = []

        # Process each source and collect all articles
        for source in active_sources:
            logger.info(f"Processing source: {source.name}")
            articles = self.parse_source(source)
            if articles:
                all_articles.extend(articles)

        # Calculate total articles using list length
        total_articles = len(all_articles)
        logger.info(f"Parsed {total_articles} articles from {total_sources} sources")

        return total_sources, all_articles

    def parse_source(self, source: Source) -> List[Dict]:
        """
        Parse RSS feed for a specific source

        Args:
            source: Source model instance

        Returns:
            List of parsed articles
        """
        try:
            logger.info(f"Fetching RSS feed from: {source.rss_url}")
            feed = feedparser.parse(source.rss_url)

            if hasattr(feed, 'bozo_exception'):
                logger.error(f"Error parsing feed {source.name}: {feed.bozo_exception}")
                return []

            if not feed.entries:
                logger.warning(f"No entries found in feed: {source.name}")
                return []

            # Process entries and filter out None results
            articles = [article for entry in feed.entries
                        if (article := self._process_entry(entry, source)) is not None]

            # Count articles using list length
            count = len(articles)

            logger.info(f"Parsed {count} articles from {source.name}")
            return articles

        except RequestException as e:
            logger.error(f"Request error for {source.name}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error parsing {source.name}: {str(e)}")
            return []

    def _process_entry(self, entry, source: Source) -> Optional[Dict]:
        """
        Process a single RSS entry and convert to article dict using site configuration

        Args:
            entry: RSS feed entry
            source: Source model instance

        Returns:
            Dictionary containing article data or None if processing failed
        """
        try:
            # Extract URL
            url = getattr(entry, 'link', None)
            if not url:
                logger.warning("Entry has no URL, skipping")
                return None

            # Check if this URL already exists in the database
            if News.objects.filter(url=url).exists():
                logger.debug(f"Article with URL {url} already exists, skipping")
                return None

            # Extract title
            title = getattr(entry, 'title', "Untitled")

            # Get site configuration based on URL
            site_config = self._get_site_config(url, source.name)

            # Extract full content using the site configuration
            content = self._extract_content(entry, url, site_config)

            # Get site category using the site configuration
            site_category = self._extract_category(entry, site_config)

            # Get tags using the site configuration
            tags = self._extract_tags(entry, site_config)

            # Create article dictionary
            article = {
                "title": title,
                "content": content,
                "url": url,
                "source": source.name,
                "site_category": site_category,
                "tags": tags
            }

            return article

        except Exception as e:
            logger.error(f"Error processing entry: {str(e)}")
            return None

    def _get_site_config(self, url: str, source_name: str) -> Dict:
        """
        Get site configuration based on URL or source name, inheriting missing or empty
        configuration sections from the default configuration

        Args:
            url: Article URL
            source_name: Name of the source

        Returns:
            Site configuration dictionary with inherited defaults where needed
        """
        domain = urlparse(url).netloc
        default_config = self.SITE_CONFIGS["default"]

        # First check for exact source name match, then domain patterns
        for config_key, config in self.SITE_CONFIGS.items():
            if config_key == "default":
                continue

            # Check if source name matches
            if config["name"] == source_name:
                matched_config = config
                break

            # Check domain patterns
            if any(pattern in domain for pattern in config["domain_patterns"]):
                matched_config = config
                break
        else:  # If loop completes without a break
            # If no match found, use default config
            return default_config

        # Create a merged configuration dictionary
        merged_config = {
            key: matched_config.get(key) or default_value
            for key, default_value in default_config.items()
        }

        return merged_config

    def _extract_content(self, entry, url: str, site_config: Dict) -> str:
        """
        Extract full content from the entry using site configuration

        Args:
            entry: RSS feed entry
            url: Article URL
            site_config: Site configuration dictionary

        Returns:
            Cleaned full content of the article
        """
        content = ""

        # Try each content extractor in order
        for extractor in site_config["content_extractors"]:
            try:
                content = extractor(entry)
                if content:
                    break
            except Exception as e:
                logger.debug(f"Content extractor error: {str(e)}")
                continue

        # Apply content cleaners
        content = self._clean_content(content, site_config)

        return content

    def _extract_tags(self, entry, site_config: Dict) -> List[str]:
        """
        Extract tags from the entry using site configuration

        Args:
            entry: RSS feed entry
            site_config: Site configuration dictionary

        Returns:
            List of tags in lowercase
        """
        tags = []

        # Try each tag extractor in order
        for extractor in site_config["tag_extractors"]:
            try:
                extracted_tags = extractor(entry)
                if extracted_tags:
                    # Convert all tags to lowercase
                    tags.extend([tag.lower() for tag in extracted_tags])
                    break
            except Exception as e:
                logger.debug(f"Tag extractor error: {str(e)}")
                continue

        return tags

    def _extract_category(self, entry, site_config: Dict) -> str:
        """
        Extract category from the entry using site configuration

        Args:
            entry: RSS feed entry
            site_config: Site configuration dictionary

        Returns:
            Category string in lowercase
        """
        category = ""

        # Try each category extractor in order
        for extractor in site_config["category_extractors"]:
            try:
                extracted_category = extractor(entry)
                if extracted_category:
                    # Convert category to lowercase
                    category = extracted_category.lower()
                    break
            except Exception as e:
                logger.debug(f"Category extractor error: {str(e)}")
                continue

        return category

    def _clean_content(self, content: str, site_config: Dict) -> str:
        """
        Clean article content from HTML tags and other unwanted elements

        Args:
            content: Raw article content
            site_config: Site configuration dictionary

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

        # Apply site-specific content cleaners
        for cleaner in site_config["content_cleaners"]:
            try:
                text = cleaner(text)
            except Exception as e:
                logger.debug(f"Content cleaner error: {str(e)}")
                continue

        return text


def run_rss_parser() -> Tuple[int, List[Dict]]:
    """
    Run the RSS parser to fetch news articles

    Returns:
        Tuple containing count of processed sources and list of parsed articles
    """
    parser = RSSParser()
    return parser.parse_all_active_sources()


if __name__ == "__main__":
    # This allows running the script directly for testing
    sources, articles = run_rss_parser()
    print(f"Processed {sources} sources and found {len(articles)} new articles")
