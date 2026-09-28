import os
from celery import Celery

# Définir le module de paramètres Django par défaut pour 'celery'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erpfinancestock.settings')

app = Celery('erpfinancestock')

# Charger la configuration depuis les settings de Django avec le préfixe CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Découvrir automatiquement les tâches dans tous les apps installés (tasks.py)
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')