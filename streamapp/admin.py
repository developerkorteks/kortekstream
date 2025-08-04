from django.contrib import admin
from django.utils.html import format_html
from .models import Advertisement, SiteConfiguration, APIEndpoint, APIMonitor

# Register your models here.

@admin.register(APIEndpoint)
class APIEndpointAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'source_domain', 'priority', 'is_active', 'updated_at')
    list_filter = ('is_active', 'source_domain')
    search_fields = ('name', 'url', 'source_domain')
    list_editable = ('priority', 'is_active')
    ordering = ('-priority', 'name')
    fieldsets = (
        ('Informasi API', {
            'fields': ('name', 'url', 'source_domain')
        }),
        ('Pengaturan', {
            'fields': ('priority', 'is_active')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """
        Override save_model untuk membersihkan cache saat endpoint diubah.
        """
        super().save_model(request, obj, form, change)
        # Force refresh cache
        obj._clear_all_api_cache()
        self.message_user(request, f"API endpoint '{obj.name}' berhasil disimpan dan cache dibersihkan.")
    
    def delete_model(self, request, obj):
        """
        Override delete_model untuk membersihkan cache saat endpoint dihapus.
        """
        name = obj.name
        obj._clear_all_api_cache()
        super().delete_model(request, obj)
        self.message_user(request, f"API endpoint '{name}' berhasil dihapus dan cache dibersihkan.")
    
    def delete_queryset(self, request, queryset):
        """
        Override delete_queryset untuk membersihkan cache saat multiple endpoints dihapus.
        """
        for obj in queryset:
            obj._clear_all_api_cache()
        super().delete_queryset(request, queryset)
        self.message_user(request, f"{queryset.count()} API endpoint(s) berhasil dihapus dan cache dibersihkan.")
    
    def get_deleted_objects(self, objs, request):
        """
        Override untuk menampilkan pesan yang lebih jelas tentang objek terkait yang akan dihapus.
        """
        deleted_objects, model_count, perms_needed, protected = super().get_deleted_objects(objs, request)
        # Hapus perms_needed untuk APIMonitor
        if 'APIMonitor' in perms_needed:
            perms_needed.remove('APIMonitor')
        return deleted_objects, model_count, perms_needed, protected

class APIMonitorAdmin(admin.ModelAdmin):
    list_display = ('get_endpoint_name', 'endpoint_path', 'get_status_colored', 'get_response_time', 'last_checked')
    list_filter = ('status', 'endpoint')
    search_fields = ('endpoint__name', 'endpoint_path')
    readonly_fields = ('endpoint', 'endpoint_path', 'status', 'response_time', 'last_checked', 'error_message', 'response_data')
    
    def get_endpoint_name(self, obj):
        return obj.endpoint.name
    get_endpoint_name.short_description = "API Endpoint"
    
    def get_status_colored(self, obj):
        colors = {
            'up': 'green',
            'down': 'red',
            'error': 'orange',
            'timeout': 'orange',
            'unknown': 'gray'
        }
        color = colors.get(obj.status, 'gray')
        return format_html('<span style="color: {};">{}</span>', color, obj.status)
    get_status_colored.short_description = "Status"
    
    def get_response_time(self, obj):
        if obj.response_time is None:
            return '-'
        return f"{obj.response_time:.2f} ms"
    get_response_time.short_description = "Waktu Respons"
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Izinkan admin untuk menghapus APIMonitor
        return request.user.is_superuser

admin.site.register(APIMonitor, APIMonitorAdmin)

@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    list_display = ('name', 'key', 'value', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'key', 'value')
    list_editable = ('is_active',)
    fieldsets = (
        ('Informasi Konfigurasi', {
            'fields': ('name', 'key', 'value', 'description')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ('name', 'provider', 'position', 'is_active', 'priority')
    list_filter = ('provider', 'position', 'is_active')
    search_fields = ('name', 'ad_code')
    list_editable = ('is_active', 'priority')
    fieldsets = (
        ('Informasi Iklan', {
            'fields': ('name', 'provider', 'ad_code')
        }),
        ('Penempatan', {
            'fields': ('position', 'max_width', 'max_height')
        }),
        ('Status', {
            'fields': ('is_active', 'priority', 'start_date', 'end_date')
        }),
    )
