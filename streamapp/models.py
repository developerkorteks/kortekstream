from django.db import models
from django.core.cache import cache
from django.utils import timezone
import requests
import logging
import json

logger = logging.getLogger(__name__)

# Create your models here.

class APIEndpoint(models.Model):
    """
    Model untuk menyimpan URL API dengan prioritas dan domain sumber.
    API dengan prioritas lebih tinggi akan dicoba terlebih dahulu.
    """
    name = models.CharField(max_length=100, verbose_name="Nama API")
    url = models.URLField(max_length=255, verbose_name="URL API")
    source_domain = models.CharField(max_length=255, verbose_name="Domain Sumber Data", default="v1.samehadaku.how", help_text="Domain sumber data yang digunakan untuk memformat URL gambar dan link")
    priority = models.IntegerField(default=0, verbose_name="Prioritas (semakin tinggi semakin diprioritaskan)")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Dibuat pada")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Diperbarui pada")
    
    class Meta:
        verbose_name = "API Endpoint"
        verbose_name_plural = "API Endpoints"
        ordering = ['-priority', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.url})"
    
    def save(self, *args, **kwargs):
        """
        Override save method untuk menghapus cache saat endpoint diubah.
        """
        super().save(*args, **kwargs)
        # Hapus cache untuk daftar API endpoints
        cache.delete("api_endpoints")
    
    @classmethod
    def get_active_endpoints(cls):
        """
        Mendapatkan semua endpoint API yang aktif, diurutkan berdasarkan prioritas.
        Menggunakan cache untuk meningkatkan performa.
        """
        from django.db.utils import OperationalError
        
        # Coba ambil dari cache terlebih dahulu
        cache_key = "api_endpoints"
        cached_endpoints = cache.get(cache_key)
        if cached_endpoints is not None:
            return cached_endpoints
        
        try:
            # Jika tidak ada di cache, ambil dari database
            endpoints = list(cls.objects.filter(is_active=True).order_by('-priority'))
            # Simpan ke cache
            cache.set(cache_key, endpoints, 3600)  # Cache selama 1 jam
            return endpoints
        except OperationalError:
            # Jika tabel belum ada (saat migrasi), kembalikan list kosong
            logger.warning("Tabel APIEndpoint belum ada (kemungkinan saat migrasi)")
            return []


class APIMonitor(models.Model):
    """
    Model untuk menyimpan status dan metrik API.
    """
    endpoint = models.ForeignKey(
        APIEndpoint,
        on_delete=models.CASCADE,  # Gunakan CASCADE agar ketika endpoint dihapus, monitor juga dihapus
        related_name="monitors",
        verbose_name="API Endpoint"
    )
    endpoint_path = models.CharField(max_length=255, verbose_name="Endpoint Path")
    status = models.CharField(max_length=20, verbose_name="Status", default="unknown")
    response_time = models.FloatField(verbose_name="Waktu Respons (ms)", null=True, blank=True)
    last_checked = models.DateTimeField(verbose_name="Terakhir Diperiksa", auto_now=True)
    error_message = models.TextField(verbose_name="Pesan Error", null=True, blank=True)
    response_data = models.TextField(verbose_name="Data Respons", null=True, blank=True)
    
    class Meta:
        verbose_name = "API Monitor"
        verbose_name_plural = "API Monitors"
        ordering = ['-last_checked']
        unique_together = ('endpoint', 'endpoint_path')
    
    def __str__(self):
        return f"{self.endpoint.name} - {self.endpoint_path} ({self.status})"
    
    @classmethod
    def check_endpoint(cls, endpoint, path, custom_url=None):
        """
        Memeriksa status endpoint API.
        
        Args:
            endpoint: APIEndpoint instance
            path: Endpoint path
            custom_url: URL kustom untuk digunakan (opsional)
            
        Returns:
            APIMonitor instance
        """
        from django.db.utils import OperationalError
        
        # Gunakan custom_url jika disediakan, jika tidak buat URL dari endpoint dan path
        url = custom_url if custom_url else f"{endpoint.url.rstrip('/')}/{path.lstrip('/')}"
        status = "unknown"
        response_time = None
        error_message = None
        response_data = None
        
        try:
            # Coba dapatkan atau buat monitor
            try:
                monitor, created = cls.objects.get_or_create(
                    endpoint=endpoint,
                    endpoint_path=path
                )
            except OperationalError as e:
                logger.warning(f"Tabel APIMonitor belum ada (kemungkinan saat migrasi): {e}")
                # Buat objek monitor sementara
                class TempMonitor:
                    def __init__(self):
                        self.endpoint = endpoint
                        self.endpoint_path = path
                        self.status = "unknown"
                        self.response_time = None
                        self.error_message = None
                        self.response_data = None
                        self.last_checked = timezone.now()
                        
                    def save(self):
                        # Metode dummy untuk save
                        logger.debug("TempMonitor.save() dipanggil (tidak ada aksi)")
                        pass
                        
                    # Metode untuk memungkinkan penugasan atribut
                    def __setattr__(self, name, value):
                        self.__dict__[name] = value
                
                monitor = TempMonitor()
            
            # Periksa endpoint
            try:
                start_time = timezone.now()
                response = requests.get(url, timeout=5)
                end_time = timezone.now()
                
                # Hitung waktu respons dalam milidetik
                response_time = (end_time - start_time).total_seconds() * 1000
                
                # Update status monitor
                monitor.response_time = response_time
                
                if response.status_code >= 200 and response.status_code < 300:
                    status = "up"
                    monitor.status = status
                    monitor.error_message = None
                    
                    # Simpan sebagian data respons (maksimal 1000 karakter)
                    try:
                        response_data = response.json()
                        monitor.response_data = json.dumps(response_data)[:1000]
                    except:
                        monitor.response_data = response.text[:1000]
                else:
                    status = "error"
                    monitor.status = status
                    error_message = f"HTTP Error: {response.status_code}"
                    monitor.error_message = error_message
                    monitor.response_data = response.text[:1000]
            
            except requests.exceptions.Timeout:
                status = "timeout"
                monitor.status = status
                error_message = "Request timeout"
                monitor.error_message = error_message
                monitor.response_time = None
                monitor.response_data = None
            
            except requests.exceptions.ConnectionError:
                status = "down"
                monitor.status = status
                error_message = "Connection error"
                monitor.error_message = error_message
                monitor.response_time = None
                monitor.response_data = None
            
            except Exception as e:
                status = "error"
                monitor.status = status
                error_message = str(e)
                monitor.error_message = error_message
                monitor.response_time = None
                monitor.response_data = None
            
            # Simpan monitor
            monitor.save()
            return monitor
            
        except Exception as e:
            logger.error(f"Error saat memeriksa endpoint {url}: {e}")
            # Kembalikan objek monitor dummy jika terjadi error
            class DummyMonitor:
                def __init__(self):
                    self.endpoint = endpoint
                    self.endpoint_path = path
                    self.status = status
                    self.response_time = response_time
                    self.error_message = error_message or str(e)
                    self.response_data = response_data
            
            return DummyMonitor()


class SiteConfiguration(models.Model):
    """
    Model untuk menyimpan konfigurasi situs.
    """
    name = models.CharField(max_length=100, verbose_name="Nama Konfigurasi")
    key = models.CharField(max_length=100, unique=True, verbose_name="Kunci Konfigurasi")
    value = models.TextField(verbose_name="Nilai Konfigurasi")
    description = models.TextField(blank=True, null=True, verbose_name="Deskripsi")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Dibuat pada")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Diperbarui pada")
    
    class Meta:
        verbose_name = "Konfigurasi Situs"
        verbose_name_plural = "Konfigurasi Situs"
        ordering = ['key']
    
    def __str__(self):
        return f"{self.name} ({self.key})"
    
    def save(self, *args, **kwargs):
        """
        Override save method untuk menghapus cache saat konfigurasi diubah.
        """
        super().save(*args, **kwargs)
        # Hapus cache untuk konfigurasi ini
        cache.delete(f"site_config_{self.key}")
        # Hapus cache untuk template filter
        cache.delete(f"template_tag_site_config_{self.key}")
        # Hapus cache untuk template filter source domain
        if self.key == 'SOURCE_DOMAIN':
            cache.delete("template_filter_source_domain")
        # Hapus cache untuk semua konfigurasi
        cache.delete("all_site_configs")
    
    @classmethod
    def get_config(cls, key, default=None):
        """
        Mendapatkan nilai konfigurasi berdasarkan key.
        Menggunakan cache untuk meningkatkan performa.
        """
        # Coba ambil dari cache terlebih dahulu
        cache_key = f"site_config_{key}"
        cached_value = cache.get(cache_key)
        if cached_value is not None:
            return cached_value
        
        # Jika tidak ada di cache, ambil dari database
        try:
            config = cls.objects.get(key=key, is_active=True)
            # Simpan ke cache
            cache.set(cache_key, config.value, 3600)  # Cache selama 1 jam
            return config.value
        except cls.DoesNotExist:
            # Jika tidak ada di database, kembalikan nilai default
            return default
    
    @classmethod
    def get_all_configs(cls):
        """
        Mendapatkan semua konfigurasi aktif.
        Menggunakan cache untuk meningkatkan performa.
        """
        # Coba ambil dari cache terlebih dahulu
        cache_key = "all_site_configs"
        cached_configs = cache.get(cache_key)
        if cached_configs is not None:
            return cached_configs
        
        # Jika tidak ada di cache, ambil dari database
        configs = {config.key: config.value for config in cls.objects.filter(is_active=True)}
        # Simpan ke cache
        cache.set(cache_key, configs, 3600)  # Cache selama 1 jam
        return configs


class Advertisement(models.Model):
    """
    Model untuk menyimpan iklan yang akan ditampilkan di halaman detail episode video.
    """
    PROVIDER_CHOICES = [
        ('propeller', 'PropellerAds'),
        ('adsterra', 'Adsterra'),
        ('popcash', 'PopCash'),
        ('custom', 'Custom'),
    ]
    
    POSITION_CHOICES = [
        ('above_player', 'Di atas player video'),
        ('below_player', 'Di bawah player video'),
        ('between_info', 'Di antara informasi anime'),
        ('sidebar', 'Di sidebar'),
        ('above_download', 'Di atas download links'),
        ('between_download', 'Di antara download links'),
        ('footer', 'Di footer'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="Nama Iklan")
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, verbose_name="Penyedia Iklan")
    ad_code = models.TextField(verbose_name="Kode Iklan (HTML/JavaScript)")
    position = models.CharField(max_length=20, choices=POSITION_CHOICES, verbose_name="Posisi Iklan")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    priority = models.IntegerField(default=0, verbose_name="Prioritas (semakin tinggi semakin diprioritaskan)")
    max_width = models.CharField(max_length=20, blank=True, null=True, verbose_name="Lebar Maksimum (contoh: 100%, 300px)")
    max_height = models.CharField(max_length=20, blank=True, null=True, verbose_name="Tinggi Maksimum (contoh: auto, 250px)")
    start_date = models.DateTimeField(blank=True, null=True, verbose_name="Tanggal Mulai")
    end_date = models.DateTimeField(blank=True, null=True, verbose_name="Tanggal Berakhir")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Dibuat pada")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Diperbarui pada")
    
    class Meta:
        verbose_name = "Iklan"
        verbose_name_plural = "Iklan"
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        position_display = dict(self.POSITION_CHOICES).get(self.position, self.position)
        return f"{self.name} ({position_display})"
    
    def is_valid_date_range(self):
        """
        Memeriksa apakah iklan masih dalam rentang tanggal yang valid.
        """
        from django.utils import timezone
        now = timezone.now()
        
        if self.start_date and self.start_date > now:
            return False
        
        if self.end_date and self.end_date < now:
            return False
        
        return True
