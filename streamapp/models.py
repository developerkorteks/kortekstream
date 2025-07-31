from django.db import models
from django.core.cache import cache

# Create your models here.

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
