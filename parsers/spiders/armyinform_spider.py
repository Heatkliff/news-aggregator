import scrapy
from datetime import datetime
from parsers.items import NewsItem
from parsers.spiders.base_spider import BaseNewsSpider


class ArmyInformSpider(BaseNewsSpider):
    """
    Spider for scraping news from ArmyInform website
    """
    name = 'armyinform'
    allowed_domains = ['armyinform.com.ua']
    
    # Map site categories to our internal category slugs
    site_categories_map = {
        'новини': 'news',
        'головне': 'main',
        'війна': 'war',
        'безпека і оборона': 'security-defense',
        'збройні сили': 'armed-forces',
        'ато': 'ato',
        'ситуація на фронті': 'front-situation',
        'оборона території': 'territory-defense',
        'громадянське суспільство': 'civil-society',
        'міжнародні відносини': 'international-relations',
        'політика': 'politics',
        'військова техніка': 'military-equipment',
        'суспільство': 'society'
    }
    
    def start_requests(self):
        """Start requests from the news category page"""
        url = 'https://armyinform.com.ua/category/news/'
        yield scrapy.Request(url=url, callback=self.parse)
    
    def parse(self, response):
        """Parse the list of news articles"""
        # Extract news article links from the page
        article_links = response.css('div.news-item h2.entry-title a::attr(href)').getall()
        
        # Follow each link to scrape the article content
        for link in article_links:
            yield scrapy.Request(url=link, callback=self.parse_article)
            
        # Follow pagination if it exists
        next_page = response.css('div.nav-links a.next.page-numbers::attr(href)').get()
        if next_page:
            yield scrapy.Request(url=next_page, callback=self.parse)
    
    def parse_article(self, response):
        """Parse a single news article"""
        item = NewsItem()
        
        # Extract title
        item['title'] = response.css('h1.entry-title::text').get().strip()
        
        # Extract content
        content_parts = response.css('div.entry-content p::text, div.entry-content p strong::text').getall()
        item['content'] = '\n\n'.join([part.strip() for part in content_parts if part.strip()])
        
        # Extract URL
        item['url'] = response.url
        
        # Set source ID
        item['source_id'] = self.source.id if self.source else None
        
        # Extract categories
        categories = []
        category_links = response.css('div.entry-meta span.cat-links a::text').getall()
        
        for category_name in category_links:
            category_id = self.get_category_id(category_name.strip())
            if category_id:
                categories.append(category_id)
        
        item['categories'] = categories
        
        # Extract tags
        tags = response.css('div.entry-meta span.tags-links a::text').getall()
        item['tags'] = [tag.strip().lower() for tag in tags if tag.strip()]
        
        # Set created_at
        item['created_at'] = datetime.now().isoformat()
        
        return item
