"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
import json
from pathlib import Path
import time


def _debug_log(hypothesis_id, location, message, data=None, run_id='initial'):
    # #region agent log
    payload = {
        'sessionId': '264829',
        'runId': run_id,
        'hypothesisId': hypothesis_id,
        'location': location,
        'message': message,
        'data': data or {},
        'timestamp': int(time.time() * 1000),
    }
    log_path = Path(__file__).resolve().parent.parent / 'debug-264829.log'
    with open(log_path, 'a', encoding='utf-8') as log_file:
        log_file.write(json.dumps(payload) + '\n')
    # #endregion


_debug_log('H2', 'config/urls.py:22', 'url configuration imported', {'media_url': settings.MEDIA_URL})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('complaints.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
