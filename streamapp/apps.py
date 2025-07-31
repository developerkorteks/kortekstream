from django.apps import AppConfig
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class StreamappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'streamapp'
    
    def ready(self):
        """
        Metode ini dijalankan saat aplikasi Django dimulai.
        Mengisi cache dengan nilai konfigurasi yang diperlukan oleh template filter.
        """
        # Import di sini untuk menghindari circular import
        from .models import SiteConfiguration
        
        try:
            # Isi cache untuk SOURCE_DOMAIN
            source_domain = SiteConfiguration.get_config('SOURCE_DOMAIN', 'v1.samehadaku.how')
            cache.set('template_filter_source_domain', source_domain, 60*60*24)  # Cache selama 24 jam
            logger.info(f"Cache filled with SOURCE_DOMAIN: {source_domain}")
            
            # Isi cache untuk konfigurasi lain yang mungkin diperlukan oleh template filter
            all_configs = SiteConfiguration.get_all_configs()
            for key, value in all_configs.items():
                cache_key = f'template_tag_site_config_{key}'
                cache.set(cache_key, value, 60*60*24)  # Cache selama 24 jam
            
            logger.info(f"Cache filled with {len(all_configs)} site configurations")
        except Exception as e:
            logger.error(f"Error filling cache with site configurations: {e}")
