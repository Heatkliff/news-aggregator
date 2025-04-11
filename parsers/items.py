import scrapy


class NewsItem(scrapy.Item):
    """
    Item representing a news article
    """
    title = scrapy.Field()
    content = scrapy.Field()
    url = scrapy.Field()
    source_id = scrapy.Field()
    categories = scrapy.Field()  # Category ID
    tags = scrapy.Field()  # List of tag names (strings)
    created_at = scrapy.Field()
