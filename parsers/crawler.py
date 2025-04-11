import os
import sys
import logging
import django
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from importlib import import_module

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'news_aggregator.settings')
django.setup()

# Import models after Django setup
from news.models import Source


def get_spider_class(source_url):
    """
    Determine which spider class to use based on the source URL
    
    Args:
        source_url: URL of the news source
        
    Returns:
        Spider class if found, None otherwise
    """
    domain = source_url.split('//')[1].split('/')[0]
    
    if 'ukrinform.ua' in domain:
        from parsers.spiders.ukrinform_spider import UkrinformSpider
        return UkrinformSpider
    elif 'armyinform.com.ua' in domain:
        from parsers.spiders.armyinform_spider import ArmyInformSpider
        return ArmyInformSpider
    elif 'tax.gov.ua' in domain:
        from parsers.spiders.tax_spider import TaxGovSpider
        return TaxGovSpider
    else:
        return None


def run_spider(source):
    """
    Run spider for a specific source
    
    Args:
        source: Source model instance
    """
    logger.info(f"Processing source: {source.name} ({source.url})")
    
    # Get the appropriate spider class
    spider_class = get_spider_class(source.url)
    
    if not spider_class:
        logger.warning(f"No custom spider found for {source.name} ({source.url})")
        return False
    
    try:
        # Set up crawler process
        process = CrawlerProcess(get_project_settings())
        
        # Add the spider with the source ID
        process.crawl(spider_class, source_id=source.id)
        
        # Start the crawling process
        process.start()
        
        logger.info(f"Completed scraping for {source.name}")
        return True
    except Exception as e:
        logger.error(f"Error scraping {source.name}: {str(e)}")
        return False


def run_all_spiders():
    """
    Run spiders for all sources that need scraping
    """
    logger.info("Starting the news scraping process")
    
    # Get all active sources that need scraping
    sources = Source.objects.filter(active=True, needs_scraping=True)
    
    if not sources:
        logger.info("No sources found that need scraping")
        return
    
    logger.info(f"Found {sources.count()} sources that need scraping")
    
    for source in sources:
        run_spider(source)
    
    logger.info("Completed scraping process for all sources")


if __name__ == "__main__":
    run_all_spiders()
