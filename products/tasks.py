"""
Celery tasks for background scraping.
"""
from celery import shared_task
from crawler import StoreScraper
from store_config import PCAndPartsConfig, EzoneConfig
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def scrape_store(self, store_name):
    """
    Scrape a single store.
    
    Args:
        store_name: Name of the store to scrape
    """
    try:
        logger.info(f"Starting scrape for {store_name}")
        
        # Map store names to configs
        store_configs = {
            'PC and Parts': PCAndPartsConfig,
            'Expert Zone': EzoneConfig,
        }
        
        config_class = store_configs.get(store_name)
        if not config_class:
            logger.error(f"Unknown store: {store_name}")
            return {'error': f'Unknown store: {store_name}'}
        
        config = config_class(auto_discover=True)
        scraper = StoreScraper(config)
        products = scraper.run()
        
        logger.info(f"Completed scrape for {store_name}: {len(products)} products")
        
        return {
            'store': store_name,
            'products_count': len(products),
            'stats': scraper.stats
        }
        
    except Exception as e:
        logger.error(f"Error scraping {store_name}: {e}")
        raise self.retry(exc=e, countdown=60 * 5)  # Retry after 5 minutes


@shared_task
def scrape_all_stores():
    """
    Scrape all configured stores.
    This task is scheduled to run periodically.
    """
    logger.info("Starting scheduled scrape for all stores")
    
    stores = ['PC and Parts', 'Expert Zone']
    results = []
    
    for store in stores:
        try:
            # Launch individual store scraping tasks
            result = scrape_store.delay(store)
            results.append({
                'store': store,
                'task_id': result.id
            })
        except Exception as e:
            logger.error(f"Failed to start task for {store}: {e}")
            results.append({
                'store': store,
                'error': str(e)
            })
    
    return {
        'message': f'Started scraping {len(stores)} stores',
        'results': results
    }


@shared_task
def cleanup_old_price_history(days=90):
    """
    Clean up price history older than specified days.
    
    Args:
        days: Number of days to keep (default: 90)
    """
    from django.utils import timezone
    from datetime import timedelta
    from .models import PriceHistory
    
    cutoff_date = timezone.now() - timedelta(days=days)
    deleted_count, _ = PriceHistory.objects.filter(recorded_at__lt=cutoff_date).delete()
    
    logger.info(f"Deleted {deleted_count} old price history records")
    return {'deleted': deleted_count, 'cutoff_date': cutoff_date.isoformat()}