
# Scrapy settings for your project

BOT_NAME = 'news_aggregator'

SPIDER_MODULES = ['parsers.spiders']
NEWSPIDER_MODULE = 'parsers.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests
CONCURRENT_REQUESTS = 16

# Configure a delay for requests for the same website
DOWNLOAD_DELAY = 0.5

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# Configure item pipelines
ITEM_PIPELINES = {
   'your_project.pipelines.NewsPipeline': 300,
}

# Enable and configure Splash middleware
SPLASH_URL = 'http://splash:8050'

DOWNLOADER_MIDDLEWARES = {
    'scrapy_splash.SplashCookiesMiddleware': 723,
    'scrapy_splash.SplashMiddleware': 725,
    'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
}

SPIDER_MIDDLEWARES = {
    'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
}

DUPEFILTER_CLASS = 'scrapy_splash.SplashAwareDupeFilter'

# Specify the new REQUEST_FINGERPRINTER_IMPLEMENTATION to avoid deprecation warning
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'

# Specify Firefox user-agent to avoid being blocked
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0'

# Enable logging
LOG_LEVEL = 'INFO'