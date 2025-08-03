from celery.schedules import crontab
from datetime import timedelta

# Jadwal tugas Celery
CELERY_BEAT_SCHEDULE = {
    # 'check-api-status-every-minute': {
    #     'task': 'streamapp.tasks.check_api_status',
    #     'schedule': timedelta(minutes=1),  # Setiap menit (untuk pengujian lokal)
    #     'args': (),
    # },
    'check-api-status-every-hour': {
        'task': 'streamapp.tasks.check_api_status',
        'schedule': crontab(minute='0', hour='*/1'),  # Setiap jam
        'args': (),
    },
    'check-api-status-daily': {
        'task': 'streamapp.tasks.check_api_status',
        'schedule': crontab(minute='0', hour='0'),  # Setiap hari pada tengah malam
        'args': (),
    },
    'get-api-status-summary-every-3-hours': {
        'task': 'streamapp.tasks.get_api_status_summary',
        'schedule': crontab(minute='0', hour='*/3'),  # Setiap 3 jam
        'args': (),
    },
}