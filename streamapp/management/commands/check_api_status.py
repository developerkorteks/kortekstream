import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from streamapp.tasks import check_api_status

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Memeriksa status semua API endpoint yang aktif'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Tampilkan output yang lebih detail',
        )

    def handle(self, *args, **options):
        verbose = options.get('verbose', False)
        
        if verbose:
            self.stdout.write(self.style.SUCCESS(f"Memulai pemeriksaan status API pada {timezone.now()}"))
        
        try:
            result = check_api_status()
            
            if result:
                self.stdout.write(self.style.SUCCESS("Pemeriksaan status API berhasil"))
            else:
                self.stdout.write(self.style.WARNING("Pemeriksaan status API selesai dengan peringatan"))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error saat memeriksa status API: {e}"))
            logger.error(f"Error saat menjalankan command check_api_status: {e}")
            return
        
        if verbose:
            self.stdout.write(self.style.SUCCESS(f"Pemeriksaan status API selesai pada {timezone.now()}"))