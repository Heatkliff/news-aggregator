from django.core.management.base import BaseCommand
from news.models import Source


class Command(BaseCommand):
    help = 'Load predefined news sources into the database with their specific configurations.'

    def handle(self, *args, **options):
        sources = [
            {"name": "Кореспондент", "url": "https://ua.korrespondent.net", "rss_url": "http://k.img.com.ua/rss/ua/all_news2.0.xml", "active": True, "needs_scraping": False},
            {"name": "ТСН", "url": "https://tsn.ua", "rss_url": "https://tsn.ua/rss/full.rss", "active": True, "needs_scraping": False},
            {"name": "Українська правда", "url": "https://www.pravda.com.ua", "rss_url": "https://www.pravda.com.ua/rss/view_news/", "active": True, "needs_scraping": False},
            {"name": "Радіо Свобода", "url": "https://www.radiosvoboda.org", "rss_url": "https://www.radiosvoboda.org/api/zrqitl-vomx-tpeoumq", "active": True, "needs_scraping": False},
            {"name": "Суспільне", "url": "https://suspilne.media", "rss_url": "https://suspilne.media/rss/all.rss", "active": True, "needs_scraping": False},
            {"name": "АрміяInform", "url": "https://armyinform.com.ua", "rss_url": "https://armyinform.com.ua/feed/", "active": True, "needs_scraping": False},
            {"name": "Еспресо", "url": "https://espreso.tv/", "rss_url": "https://espreso.tv/rss", "active": True, "needs_scraping": False},
            {"name": "LIGA.net", "url": "https://www.liga.net/", "rss_url": "https://www.liga.net/news/all/rss.xml", "active": True, "needs_scraping": False},
            {"name": "Лівий Берег", "url": "https://lb.ua/", "rss_url": "https://lb.ua/rss/ukr/news.xml", "active": True, "needs_scraping": False},
            {"name": "УКРІНФОРМ", "url": "https://www.ukrinform.ua/", "rss_url": "https://www.ukrinform.ua/rss/block-lastnews", "active": True, "needs_scraping": False},
            {"name": "УНІАН", "url": "https://www.unian.ua/", "rss_url": "https://rss.unian.net/site/news_ukr.rss", "active": True, "needs_scraping": False}
        ]

        for src in sources:
            source, created = Source.objects.update_or_create(
                name=src['name'],
                defaults={
                    'url': src['url'],
                    'rss_url': src['rss_url'],
                    'active': src['active'],
                    'needs_scraping': src['needs_scraping'],
                }
            )
            status = 'Created' if created else 'Updated'
            self.stdout.write(f'{status}: {source.name}')

        self.stdout.write(self.style.SUCCESS('All sources have been loaded successfully.'))
