from celery import shared_task
from django.core.management import call_command
from django.utils import timezone
from celery import chain
from django.conf import settings

from .models import LogStats


@shared_task
def parse_rss_task():
    """
    Task for running RSS parser management command
    """
    # Create initial import stats record
    import_stats = LogStats.objects.create()

    call_command('rss_parse')

    # Return the ID of the stats record to be used by the next task
    return import_stats.id


@shared_task
def import_news_task(stats_id):
    """
    Task for importing news from Redis to database
    """
    # Get the import stats record
    try:
        import_stats = LogStats.objects.get(id=stats_id)
    except LogStats.DoesNotExist:
        # Create a new record if the previous one doesn't exist for some reason
        import_stats = LogStats.objects.create()

    # Run the import command (which stores stats in settings)
    call_command('import_news_from_redis')
    
    # Get stats from Django settings or from NewsImporter directly
    if hasattr(settings, '_IMPORT_NEWS_STATS'):
        stats = getattr(settings, '_IMPORT_NEWS_STATS')
    else:
        # Fallback: directly access the NewsImporter to get stats
        from news.management.commands.import_news_from_redis import NewsImporter
        importer = NewsImporter()
        # We'd need to re-run import_news to get stats, but we know stats were 
        # collected during the call_command above, so get them via the import method
        news_data = importer.get_news_from_redis()
        for item in news_data:
            try:
                result = importer._process_single_news_item(item)
                if result:
                    importer.stats["imported"] += 1
                else:
                    importer.stats["skipped"] += 1
            except Exception:
                importer.stats["errors"] += 1
        stats = importer.stats

    # Update the stats record with the results
    import_stats.imported = stats['imported']
    import_stats.skipped = stats['skipped']
    import_stats.errors = stats['errors']
    import_stats.completed_at = timezone.now()
    import_stats.save()

    # Return the stats for logging purposes
    return {
        'stats_id': stats_id,
        'imported': stats['imported'],
        'skipped': stats['skipped'],
        'errors': stats['errors'],
        'duration': (import_stats.completed_at - import_stats.started_at).total_seconds()
    }


@shared_task
def process_news_chain():
    """
    Chain task that runs both RSS parsing and news import in sequence
    """
    # Use chain to ensure tasks run in sequence and the result of the first task is passed to the second task
    return chain(
        parse_rss_task.s(),
        import_news_task.s()
    )()