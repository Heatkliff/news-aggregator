import scrapy
from datetime import datetime
from parsers.items import NewsItem
from parsers.spiders.base_spider import BaseNewsSpider


class TaxGovSpider(BaseNewsSpider):
    """
    Spider for scraping news from the Ukrainian Tax Authority website
    """
    name = 'taxgov'
    allowed_domains = ['tax.gov.ua']
    
    # Map site categories to our internal category slugs
    site_categories_map = {
        'новини': 'news',
        'податки': 'taxes',
        'міжнародні відносини': 'international-relations',
        'підприємництво': 'entrepreneurship',
        'законодавство': 'legislation',
        'бізнес': 'business',
        'економіка': 'economy',
        'громадянам': 'for-citizens',
        'діяльність': 'activities',
        'інтерв\'ю': 'interviews',
        'регіональні': 'regional'
    }
    
    def start_requests(self):
        """Start requests from the news page"""
        url = 'https://tax.gov.ua/media-tsentr/novini/'
        yield scrapy.Request(url=url, callback=self.parse)
    
    def parse(self, response):
        """Parse the list of news articles"""
        # Extract news article links from the page
        article_links = response.css('div.news-list div.news-title a::attr(href)').getall()
        
        # Follow each link to scrape the article content
        for link in article_links:
            full_url = response.urljoin(link)
            yield scrapy.Request(url=full_url, callback=self.parse_article)
            
        # Follow pagination if it exists
        next_page = response.css('div.pager a.next::attr(href)').get()
        if next_page:
            yield scrapy.Request(url=response.urljoin(next_page), callback=self.parse)
    
    def parse_article(self, response):
        """Parse a single news article"""
        item = NewsItem()
        
        # Extract title
        item['title'] = response.css('h1.page-title::text').get().strip()
        
        # Extract content
        content_parts = response.css('div.news-detail-text p::text, div.news-detail-text p strong::text').getall()
        item['content'] = '\n\n'.join([part.strip() for part in content_parts if part.strip()])
        
        # Extract URL
        item['url'] = response.url
        
        # Set source ID
        item['source_id'] = self.source.id if self.source else None
        
        # Extract categories - Tax.gov.ua doesn't have explicit categories in article pages
        # So we need to determine categories based on the article URL structure or content
        categories = []
        
        # Check URL structure for category indicators
        url_path = response.url.split('/')
        if 'podatki' in url_path:
            category_id = self.get_category_id('податки')
            if category_id:
                categories.append(category_id)
        elif 'zakonodavstvo' in url_path:
            category_id = self.get_category_id('законодавство')
            if category_id:
                categories.append(category_id)
        elif 'diyalnist' in url_path:
            category_id = self.get_category_id('діяльність')
            if category_id:
                categories.append(category_id)
        
        # If no categories were determined from URL structure, set a default
        if not categories:
            default_category_id = self.get_category_id('новини')
            if default_category_id:
                categories.append(default_category_id)
        
        item['categories'] = categories
        
        # Extract tags - Tax.gov.ua doesn't have explicit tags
        # We can use keywords from the article content as tags
        content_lower = item['content'].lower()
        potential_tags = ['податки', 'дпс', 'фіскальна', 'єдиний податок', 'пдв', 'декларація', 'бізнес']
        
        tags = []
        for tag in potential_tags:
            if tag in content_lower:
                tags.append(tag)
        
        item['tags'] = tags
        
        # Set created_at
        item['created_at'] = datetime.now().isoformat()
        
        return item
