import scrapy
from scrapy_splash import SplashRequest
import json
from datetime import datetime
from scrapy.exceptions import CloseSpider
from .base_spider import BaseNewsSpider


class NewsItem(scrapy.Item):
    title = scrapy.Field()
    content = scrapy.Field()
    url = scrapy.Field()
    source_id = scrapy.Field()
    categories = scrapy.Field()
    tags = scrapy.Field()
    created_at = scrapy.Field()


class UkrinformSpider(BaseNewsSpider):
    """
    Spider for parsing news from https://www.ukrinform.ua/block-lastnews using Splash for JavaScript rendering
    """
    name = 'ukrinform'
    allowed_domains = ['ukrinform.ua']
    start_urls = ['https://www.ukrinform.ua/block-lastnews']
    output_file = 'ukrinform_news.json'

    # Map of site categories to internal categories
    site_categories_map = {
        'rubric-ato': 'war',
        'rubric-vidbudova': 'war',
        'rubric-polytics': 'politics',
        'rubric-economy': 'economy',
        'rubric-factcheck': 'factcheck',
        'rubric-world': 'world',
        'rubric-regions': 'regions',
        'rubric-tymchasovo-okupovani': 'war',
        'rubric-society': 'society',
        'rubric-culture': 'culture',
        'rubric-diaspora': 'diaspora',
        'rubric-sports': 'sports',
        'rubric-kyiv': 'regions'
    }

    # List to store results
    results = []

    # Custom browser headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
        'Accept-Language': 'uk,en-US;q=0.7,en;q=0.3',
    }

    # Splash Lua script to handle cookies and execute JavaScript
    lua_script = """
    function main(splash, args)
        splash:set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0')

        splash.private_mode_enabled = false
        splash:set_custom_headers(args.headers)

        local url = args.url
        assert(splash:go(url))
        assert(splash:wait(5))

        -- Log information for debugging
        splash:log("URL: " .. url)
        splash:log("Status: " .. splash:get_status_code())

        -- Execute JavaScript to handle any dynamic content
        splash:runjs("window.scrollTo(0, document.body.scrollHeight);")
        assert(splash:wait(2))

        return {
            html = splash:html(),
            url = splash:url(),
            status = splash:get_status_code(),
            cookies = splash:get_cookies(),
            headers = splash:get_all_response_headers(),
        }
    end
    """

    def start_requests(self):
        """Start requests with custom headers and Splash for JavaScript support"""
        for url in self.start_urls:
            # Try with Splash and custom Lua script
            yield SplashRequest(
                url=url,
                callback=self.parse,
                endpoint='execute',
                args={
                    'lua_source': self.lua_script,
                    'headers': self.headers,
                    'url': url
                },
                dont_filter=True,  # Important to prevent URL filtering
                meta={'dont_redirect': True}
            )

    def parse(self, response):
        """Parse the news list"""
        self.logger.info(f"Parsing URL: {response.url} with status: {response.status}")

        # Debug information
        if hasattr(response, 'data'):
            self.logger.info(f"Response status from Splash: {response.data.get('status')}")
            if 'headers' in response.data:
                self.logger.info(f"Response headers: {response.data['headers']}")

        # Extra debug - print the first 500 characters of the response body
        body_preview = response.body.decode('utf-8', errors='ignore')[:500]
        self.logger.info(f"Response body preview: {body_preview}")

        # Try several CSS selectors for article links
        selectors = [
            'div.rest a::attr(href)',
            'article h2 a::attr(href)',
            '.news-card__title a::attr(href)',
            '.news-list__article a::attr(href)',
            '.article-title a::attr(href)',
            'a.article-link::attr(href)',
            'a[href*="/rubric-"]::attr(href)',
            '.news-list a::attr(href)',
            'div.block-news a::attr(href)'
        ]

        article_links = []
        for selector in selectors:
            links = response.css(selector).getall()
            if links:
                article_links.extend(links)
                self.logger.info(f"Found {len(links)} links with selector: {selector}")

        # De-duplicate links
        article_links = list(set(article_links))

        if not article_links:
            self.logger.warning("No article links found. The page might not have loaded correctly.")
            # Try a less strict XPath selector that gets all links
            article_links = response.xpath(
                '//a[contains(@href, "/news/") or contains(@href, "/article/") or contains(@href, "/rubric-")]/@href').getall()
            if not article_links:
                # Last resort - get all links and filter
                all_links = response.xpath('//a/@href').getall()
                article_links = [link for link in all_links if
                                 '/rubric-' in link or '/article/' in link or '/news/' in link]

                if not article_links:
                    self.logger.error("Still no article links found. Raising CloseSpider.")
                    raise CloseSpider("No data to parse")

        self.logger.info(f"Found {len(article_links)} total article links after deduplication")

        # Process each article link
        for link in article_links[:20]:  # Limiting to first 20 for testing
            full_url = response.urljoin(link)
            self.logger.info(f"Will process article: {full_url}")

            yield scrapy.Request(
                url=full_url,
                callback=self.parse_article,
                headers=self.headers
            )

    def parse_article(self, response):
        """Parse an individual article"""
        self.logger.info(f"Parsing article: {response.url}")
        item = NewsItem()

        # Extract title with multiple selectors
        title_selectors = [
            'h1.newsTitle::text',
            'h1.article__title::text',
            'h1.news-title::text',
            'h1::text'
        ]

        for selector in title_selectors:
            title = response.css(selector).get()
            if title and title.strip():
                item['title'] = title.strip()
                break
        else:
            self.logger.warning(f"Title not found for {response.url}")
            item['title'] = "No title"

        # Extract article content with multiple selectors
        content_selectors = [
            'div.newsText p::text',
            'div.article-text p::text',
            'div.article__text p::text',
            'div.article-body p::text',
            'div.content p::text',
            'div[itemprop="articleBody"] p::text'
        ]

        content_parts = []
        for selector in content_selectors:
            parts = response.css(selector).getall()
            if parts:
                content_parts.extend(parts)
                self.logger.info(f"Found content with selector: {selector}")
                break

        item['content'] = '\n\n'.join([part.strip() for part in content_parts if part.strip()])
        if not item['content']:
            self.logger.warning(f"Content not found for {response.url}")
            item['content'] = "No content"

        # Extract URL
        item['url'] = response.url

        # Set source_id if source is available
        item['source_id'] = getattr(self, 'source', None) and self.source.id or None

        # Extract category from URL
        url_parts = response.url.split('/')
        category_found = False
        for part in url_parts:
            if part.startswith('rubric-'):
                category_slug = part
                internal_category = self.site_categories_map.get(category_slug)
                if internal_category:
                    item['categories'] = [internal_category]
                    category_found = True
                break
        if not category_found:
            item['categories'] = []
            self.logger.info(f"Category not found for {response.url}")

        # Extract tags with multiple selectors
        tag_selectors = [
            'aside.tags a.tag::text',
            'div.article__tags a::text',
            '.tags a::text',
            'div.tags-item a::text'
        ]

        tags = []
        for selector in tag_selectors:
            found_tags = response.css(selector).getall()
            if found_tags:
                tags.extend(found_tags)
                break

        item['tags'] = [tag.strip().lower() for tag in tags if tag.strip()]

        # Extract publication date with multiple selectors
        date_selectors = [
            'time::attr(datetime)',
            '.article__date::attr(datetime)',
            '.news-date::attr(datetime)',
            'time.date::attr(datetime)'
        ]

        date_str = None
        for selector in date_selectors:
            found_date = response.css(selector).get()
            if found_date:
                date_str = found_date
                break

        if date_str:
            item['created_at'] = date_str
        else:
            item['created_at'] = datetime.now().isoformat()
            self.logger.warning(f"Date not found for {response.url}")

        # Add the result to the list
        self.results.append(dict(item))

        return item

    def closed(self, reason):
        """Save results to a file when the spider is closed"""
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=4)
        self.logger.info(f"Results saved to {self.output_file}")