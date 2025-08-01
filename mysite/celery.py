import os
from celery import Celery

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

# Create Celery app
app = Celery('mysite')

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Pastikan direktori untuk filesystem broker ada
os.makedirs('/tmp/celery_broker/in', exist_ok=True)
os.makedirs('/tmp/celery_broker/out', exist_ok=True)
os.makedirs('/tmp/celery_broker/processed', exist_ok=True)
os.makedirs('/tmp/celery_results', exist_ok=True)

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')