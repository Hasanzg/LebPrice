"""
Django management command to run scrapers.
Usage: python manage.py scrape_stores
       python manage.py scrape_stores --store "PC and Parts"
"""
from django.core.management.base import BaseCommand
from crawler import StoreScraper
from store_config import PCAndPartsConfig, EzoneConfig


class Command(BaseCommand):
    help = 'Scrape products from configured stores'

    def add_arguments(self, parser):
        parser.add_argument(
            '--store',
            type=str,
            help='Specific store to scrape (default: all)',
        )

    def handle(self, *args, **options):
        store_configs = {
            'PC and Parts': PCAndPartsConfig,
            'Expert Zone': EzoneConfig,
        }
        
        specific_store = options.get('store')
        
        if specific_store:
            if specific_store not in store_configs:
                self.stdout.write(self.style.ERROR(f'Unknown store: {specific_store}'))
                self.stdout.write(f'Available stores: {", ".join(store_configs.keys())}')
                return
            
            configs_to_scrape = {specific_store: store_configs[specific_store]}
        else:
            configs_to_scrape = store_configs
        
        for store_name, config_class in configs_to_scrape.items():
            self.stdout.write(f'\nScraping {store_name}...')
            config = config_class(auto_discover=True)
            scraper = StoreScraper(config)
            scraper.run()
            self.stdout.write(self.style.SUCCESS(f'Completed {store_name}'))