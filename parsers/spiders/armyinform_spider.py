import json
import os
import sys
from datetime import datetime
import random
from twisted.internet import selectreactor
selectreactor.install()
import scrapy
from scrapy.utils.response import open_in_browser  # Для дебагу

try:
    from .base_spider import BaseNewsSpider
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from base_spider import BaseNewsSpider

class ArmyInformSpider(BaseNewsSpider):
    """
    Spider for scraping news from armyinform.com.ua
    """
    name = 'armyinform_spider'
    allowed_domains = ['armyinform.com.ua']
    start_urls = ['https://armyinform.com.ua/category/news/']

    # Список User-Agent для ротації
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    ]

    site_categories_map = {
        'news': 'news',
    }

    def __init__(self, *args, **kwargs):
        proxy = kwargs.pop('proxy', None)
        super(ArmyInformSpider, self).__init__(*args, **kwargs)

        self.custom_settings = {
            'USER_AGENT': random.choice(self.user_agents),  # Ротація User-Agent
            'COOKIES_ENABLED': True,
            'DOWNLOAD_DELAY': 5,  # Збільшено затримку
            'RANDOMIZE_DOWNLOAD_DELAY': True,
            'DOWNLOAD_TIMEOUT': 60,  # Збільшено тайм-аут
            'RETRY_TIMES': 10,
            'RETRY_HTTP_CODES': [500, 502, 503, 504, 522, 524, 408, 429, 403],
            'CONCURRENT_REQUESTS': 2,  # Помірна паралельність
            'DOWNLOADER_CLIENT_TLS_METHOD': 'TLSv1.2+',  # Сучасні TLS-версії
            'TWISTED_REACTOR': 'twisted.internet.selectreactor.SelectReactor',
            'DEFAULT_REQUEST_HEADERS': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
            },
            'LOG_LEVEL': 'DEBUG',  # Детальні логи для дебагу
            'HTTPERROR_ALLOWED_CODES': [403, 429],  # Дозволяємо обробляти ці коди
        }

        if proxy:
            self.logger.info(f"Using proxy: {proxy}")
            self.custom_settings['PROXY'] = proxy

    def parse(self, response):
        """
        Parse the news listing page and extract article links
        """
        self.logger.info(f"Processing news listing page: {response.url}")

        # Для дебагу: відкрити сторінку в браузері
        # open_in_browser(response)

        article_links = response.css('div.archive-item h2.entry-title a::attr(href)').getall()

        if not article_links:
            self.logger.warning(f"No article links found on page: {response.url}")
            self.logger.debug(f"Page content: {response.text[:1000]}...")
        else:
            self.logger.info(f"Found {len(article_links)} article links")

        for link in article_links:
            self.logger.debug(f"Following article link: {link}")
            yield scrapy.Request(
                url=link,
                callback=self.parse_article,
                errback=self.errback_handler,
                meta={'dont_retry': False, 'max_retry_times': 10}
            )

        next_page = response.css('a.next.page-numbers::attr(href)').get()
        if next_page:
            self.logger.info(f"Following next page: {next_page}")
            yield scrapy.Request(
                url=next_page,
                callback=self.parse,
                errback=self.errback_handler,
                meta={'dont_retry': False, 'max_retry_times': 10}
            )

    def parse_article(self, response):
        """
        Parse individual article pages
        """
        self.logger.info(f"Processing article: {response.url}")

        title = response.css('h1.entry-title::text').get() or response.css('header h1::text').get() or "No title found"
        title = title.strip()

        content_sections = response.css('div.single-content p')
        content_texts = [' '.join(section.css('*::text').getall()).strip() for section in content_sections if section.css('*::text').getall()]
        content = '\n\n'.join(content_texts)

        if not content:
            self.logger.warning(f"No content found for article: {response.url}")
            content_raw = response.css('div.single-content').get()
            if content_raw:
                import re
                content_texts = re.findall(r'>([^<>]+)<', content_raw)
                content = '\n\n'.join([t.strip() for t in content_texts if t.strip()]) or "No content found"

        tags = [tag.strip() for tag in response.css('div.tags-area a::text').getall() if tag.strip()]
        slug = response.url.split('/')[-2]

        item = {
            'title': title,
            'slug': slug,
            'content': content,
            'tags': tags,
            'url': response.url,
            'site_category': 'news',
            'source': 'armyinform',
            'created_at': datetime.now().isoformat()
        }

        self.logger.info(f"Successfully scraped article: {title}")
        self.save_to_json(item)
        return item

    def errback_handler(self, failure):
        """
        Handle request errors
        """
        request = failure.request
        self.logger.error(f"Error on {request.url}: {repr(failure)}")
        if hasattr(failure.value, 'response') and failure.value.response:
            self.logger.error(f"Error {failure.value.response.status} on {request.url}")
            self.logger.debug(f"Response headers: {failure.value.response.headers}")

    def save_to_json(self, item):
        """
        Save scraped item to JSON file
        """
        try:
            filename = self.get_output_filename() or 'armyinform_news.json'
            items = []
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    items = json.load(f)
            items.append(item)
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(items, f, ensure_ascii=False, indent=4)
            self.logger.info(f"Saved item to {filename}")
        except Exception as e:
            self.logger.error(f"Error saving to JSON: {e}")