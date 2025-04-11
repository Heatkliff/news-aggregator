import logging
import os
import sys
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def scrape_news():
    """
    Celery task to scrape news from all configured sources
    """
    logger.info("Starting scheduled news scraping task")

    # Add the project directory to the Python path
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # Import here to avoid circular imports
    from parsers.crawler import run_all_spiders

    try:
        run_all_spiders()
        logger.info("Completed scheduled news scraping task")
        return True
    except Exception as e:
        logger.error(f"Error during scheduled news scraping: {str(e)}")
        return False


@shared_task
def scrape_specific_source(source_id):
    """
    Celery task to scrape news from a specific source

    Args:
        source_id: ID of the source to scrape
    """
    logger.info(f"Starting news scraping task for source ID: {source_id}")

    # Add the project directory to the Python path
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # Import here to avoid circular imports
    from parsers.crawler import run_spider
    from news.models import Source

    try:
        source = Source.objects.get(id=source_id)
        result = run_spider(source)
        if result:
            logger.info(f"Successfully scraped source: {source.name}")
        else:
            logger.warning(f"Failed to scrape source: {source.name}")
        return result
    except Source.DoesNotExist:
        logger.error(f"Source with ID {source_id} does not exist")
        return False
    except Exception as e:
        logger.error(f"Error during news scraping for source ID {source_id}: {str(e)}")
        return False