import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from parsers.rss.rss import run_rss_parser


class Command(BaseCommand):
    """
    Management command to parse RSS feeds and save the results to a JSON file
    """
    help = 'Parse RSS feeds from active sources and save results to JSON'

    def add_arguments(self, parser):
        """
        Add command line arguments
        """
        parser.add_argument(
            '--output',
            type=str,
            default='parsed_news.json',
            help='Path to the output JSON file'
        )

    def handle(self, *args, **options):
        """
        Execute the command
        """
        output_file = options['output']

        # If the output path is not absolute, make it relative to the project base
        if not os.path.isabs(output_file):
            output_file = os.path.join(settings.BASE_DIR, output_file)

        self.stdout.write(self.style.SUCCESS(f"Starting RSS parsing..."))

        try:
            sources, articles = run_rss_parser(
                output_file=output_file
            )

            if sources == 0:
                self.stdout.write(self.style.WARNING("No sources were processed."))
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully processed {sources} source(s) and found {articles} article(s)"
                    )
                )

            if articles > 0:
                self.stdout.write(
                    self.style.SUCCESS(f"Results saved to: {output_file}")
                )
            else:
                self.stdout.write(self.style.WARNING("No articles found, JSON file not created"))

        except Exception as e:
            raise CommandError(f"Error during RSS parsing: {str(e)}")
